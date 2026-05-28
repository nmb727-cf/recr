import logging
from django.utils import timezone
from apps.orchestration_center.services.workflow_engine import WorkflowEngine
from apps.orchestration_center.models.workflow import WorkflowTemplate
from apps.jobs.models import JobRequisition, JobStage

logger = logging.getLogger(__name__)

class JobWorkflowService:
    @staticmethod
    def trigger_job_workflow(requisition, event_type, context=None):
        """
        Triggers Workflow Master for a job.
        If job has a specific workflow_id, we trigger that.
        Otherwise, we look for workflows matching the event_type for the tenant.
        """
        workflow_enabled = bool(getattr(requisition, 'workflow_enabled', False))
        if not workflow_enabled and event_type != 'job.created':
            # We always trigger job.created to see if a workflow should be attached
            return []

        tenant_id = requisition.tenant_id
        
        # Build context
        workflow_context = {
            'requisition_id': str(requisition.id),
            'job_title': getattr(requisition, 'title', ''),
            'job_status': getattr(requisition, 'status', ''),
            'hiring_manager_id': str(getattr(requisition, 'hiring_manager_id', '') or '') or None,
            'recruiter_id': str(getattr(requisition, 'recruiter_id', '') or '') or None,
            'department_id': str(getattr(requisition, 'department_id', '') or '') or None,
        }
        if context:
            workflow_context.update(context)

        # Trigger Workflow Engine
        executions = WorkflowEngine.trigger_workflows(
            tenant_id=tenant_id,
            trigger_event=event_type,
            entity_type='job',
            entity_id=requisition.id,
            context_data=workflow_context
        )
        
        if executions and event_type == 'job.created':
            # If a workflow was started on creation, bind it if not already bound
            if not requisition.workflow_id:
                requisition.workflow_id = executions[0].workflow_id
                requisition.workflow_enabled = True
                requisition.save(update_fields=['workflow_id', 'workflow_enabled'])
                
                # Sync pipeline immediately if template defines stages
                JobWorkflowService.sync_job_pipeline(requisition)
        
        return executions

    @staticmethod
    def sync_job_pipeline(requisition):
        """
        Derives JobStage records from the attached WorkflowTemplate.
        If is_workflow_controlled is True, this is the source of truth.
        """
        if not requisition.workflow_enabled or not requisition.workflow_template_id:
            return

        try:
            template = WorkflowTemplate.objects.get(id=requisition.workflow_template_id)
            workflow_stages = template.workflow_stages or []
            
            if not workflow_stages:
                return

            # Deactivate existing stages that aren't in the workflow
            # (or we could just mark them as controlled)
            JobStage.objects.filter(requisition_id=requisition.id).update(is_active=False)

            for idx, stage_cfg in enumerate(workflow_stages):
                role = stage_cfg.get('responsible_role', 'recruiter')
                st_type = stage_cfg.get('type', 'screening')
                
                # Default authority logic if not in template
                authority = stage_cfg.get('decision_authority')
                if not authority:
                    if st_type == 'offer':
                        authority = 'hiring_manager'
                    elif st_type == 'joined':
                        authority = 'admin'
                    else:
                        authority = 'any'

                user_id = stage_cfg.get('responsible_user_id')
                
                # If role is specified but no specific user, try to derive from requisition
                if not user_id:
                    if role == 'hiring_manager':
                        user_id = requisition.hiring_manager_id
                    elif role == 'recruiter':
                        user_id = requisition.recruiter_id
                    elif role == 'coordinator':
                        user_id = requisition.coordinator_id

                JobStage.objects.update_or_create(
                    requisition_id=requisition.id,
                    name=stage_cfg['name'],
                    tenant_id=requisition.tenant_id,
                    defaults={
                        'stage_order': idx + 1,
                        'stage_type': stage_cfg.get('type', 'screening'),
                        'action_deadline_hours': stage_cfg.get('deadline_hours', 48),
                        'sla_target_hours': stage_cfg.get('sla_hours', 24),
                        'responsible_role': role,
                        'decision_authority': authority,
                        'responsible_user_id': user_id,
                        'is_active': True,
                        'metadata': {
                            'workflow_controlled': True,
                            'workflow_node_id': stage_cfg.get('node_id')
                        }
                    }
                )
            logger.info(f"Synced pipeline for Job {requisition.id} from Workflow {template.name}")
        except WorkflowTemplate.DoesNotExist:
            logger.error(f"WorkflowTemplate {requisition.workflow_template_id} not found for sync")
        except Exception as e:
            logger.error(f"Error syncing pipeline for job {requisition.id}: {e}")

    @staticmethod
    def can_move_to_stage(requisition, application, target_stage, user=None):
        """
        Enforce workflow movement rules and decision authority.
        Hierarchy: Workflow Master > Job Config > Module Automation.
        """
        if not user:
            # Allow system/automation overrides
            return True, ""

        if not requisition.is_workflow_controlled:
            # Basic authority check even if not workflow controlled
            pass

        # 1. Authority Check
        authority = target_stage.decision_authority
        is_authorized = False

        if authority == 'any':
            is_authorized = True
        elif authority == 'hiring_manager' and str(user.id) == str(requisition.hiring_manager_id):
            is_authorized = True
        elif authority == 'recruiter' and str(user.id) == str(requisition.recruiter_id):
            is_authorized = True
        elif authority == 'coordinator' and str(user.id) == str(requisition.coordinator_id):
            is_authorized = True
        elif authority == 'admin' and (str(user.id) == str(requisition.job_owner_id) or user.is_staff):
            is_authorized = True

        if not is_authorized and authority != 'any':
            return False, f"Decision Authority restricted to {authority.replace('_', ' ').title()} for stage '{target_stage.name}'."

        # 2. Sequence Logic
        current_stage = JobStage.objects.filter(id=application.current_stage_id).first()
        
        # Rule 1: No stage skipping (must follow workflow_stages order)
        if current_stage:
            if target_stage.stage_order > current_stage.stage_order + 1:
                return False, f"Workflow Master prevents skipping to '{target_stage.name}'. Next allowed stage is needed."
            
            # Rule 2: Backward movement restriction
            if target_stage.stage_order < current_stage.stage_order:
                # We could allow this if specifically configured in workflow
                return False, f"Workflow Master prevents backward movement to '{target_stage.name}'."

        # Rule 3: Initial stage must be the first workflow stage
        if not current_stage and target_stage.stage_order > 1:
             return False, "Candidate must enter the workflow at the first defined stage."

        return True, ""

    @staticmethod
    def handle_fallback(requisition, stage_name, module_type):
        """
        If Workflow Master doesn't handle a specific stage/action,
        we fallback to module-level automation or job config.
        Hierarchy: Workflow Master > Job Config > Module Default.
        """
        logger.info(f"Fallback check for Job {requisition.id}, Stage: {stage_name}, Module: {module_type}")
        
        # 1. Job Creation / Setup
        if module_type == 'job_creation':
            return False

        # 2. Assignment
        if module_type == 'recruiter_assignment':
            return requisition.auto_assign_recruiter
        if module_type == 'agency_assignment':
            return False

        # 3. Screening & Pipeline
        if module_type == 'prequal':
            return requisition.prequal_enabled
        if module_type == 'interview':
            # Check if interview package is bound
            from apps.interviews.models import InterviewPackageBinding
            return InterviewPackageBinding.objects.filter(job_id=requisition.id, is_deleted=False).exists()
            
        # 4. Post-Hiring
        if module_type == 'onboarding':
            return requisition.hiring_complete_action == 'auto_onboarding'

        # 5. Generic Module Automation (fallback for AutomationEngine)
        if module_type == 'module_automation':
            # In a workflow-controlled job, we generally disable standalone module rules 
            # unless it's an event the workflow doesn't care about.
            # For now, let's say if workflow is active, module rules are restricted.
            return not requisition.workflow_enabled or not requisition.is_workflow_controlled

        return True
