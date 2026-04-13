from apps.accounts.models import CustomUser
from apps.jobs.models import JobRequisition

def resolve_job_owner(job):
    """
    Resolves the actual job owner with fallback logic.
    1. If explicit job_owner_id exists and is active -> use as Job Owner
    2. If created_by exists and is active -> use as Job Owner
    3. Fallback to first active Tenant Admin of the same tenant
    """
    # 1. Explicit Owner
    owner_id = job.job_owner_id
    if owner_id:
        owner = CustomUser.objects.filter(id=owner_id, is_active=True, is_deleted=False).first()
        if owner:
            return owner

    # 2. Creator
    creator_id = job.created_by
    if creator_id:
        creator = CustomUser.objects.filter(id=creator_id, is_active=True, is_deleted=False).first()
        if creator:
            return creator
    
    # Fallback to Tenant Admin
    fallback_admin = CustomUser.objects.filter(
        tenant_id=job.tenant_id,
        role='tenant_admin',
        is_active=True,
        is_deleted=False
    ).first()
    
    return fallback_admin

def can_perform_job_action(action, job, user):
    """
    Centralized helper for Job actions.
    Supports isJobOwner, isTenantAdmin, isSuperAdmin.
    """
    if not user or not user.is_authenticated:
        return False
        
    # Super Admin can do anything
    if user.role == 'super_admin':
        return True
        
    # Tenant Admin can do anything within their tenant
    if user.role == 'tenant_admin' and str(user.tenant_id) == str(job.tenant_id):
        return True
        
    # Resolve Job Owner
    resolved_owner = resolve_job_owner(job)
    if resolved_owner and str(user.id) == str(resolved_owner.id):
        return True
        
    # Specific permission check can be added here if role-based permissions are required
    # But for ownership-locked actions, we rely on the logic above
    
    return False

def is_automation_actor(user):
    """
    Check if the actor is a system automation or threshold automation.
    """
    if not user:
        return True

    role = str(getattr(user, 'role', '') or '').lower()
    if role in {'system', 'automation'}:
        return True

    metadata = getattr(user, 'metadata', {}) or {}
    actor_mode = str(metadata.get('actor_mode', '') or '').lower()
    trigger = str(metadata.get('workflow_trigger', '') or '').lower()
    if actor_mode in {'system_automation', 'threshold_automation'}:
        return True
    if trigger in {'approved_threshold', 'approved_threshold_automation'}:
        return True

    return False
