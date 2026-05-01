import uuid
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from apps.pipeline.models import Application, ApplicationStageHistory, ActionDeadline, Placement
from apps.jobs.models import JobRequisition, JobStage
from apps.interviews.models import Interview

class JobIntelligenceEngine:
    @staticmethod
    def get_job_intelligence(tenant_id, requisition_id):
        job = JobRequisition.objects.get(id=requisition_id, tenant_id=tenant_id)
        apps = Application.objects.filter(requisition_id=requisition_id, tenant_id=tenant_id, is_deleted=False)
        total_apps = apps.count()
        
        # 1. Hiring Velocity (Step 3)
        velocity = JobIntelligenceEngine._calculate_velocity(job, apps)
        
        # 2. Bottlenecks (Step 4)
        bottlenecks = JobIntelligenceEngine._detect_bottlenecks(job, apps)
        
        # 3. Job Health Model (Step 2)
        health = JobIntelligenceEngine._calculate_health(job, apps, velocity, bottlenecks)
        
        # 4. Source Intelligence (Step 5)
        source_intel = JobIntelligenceEngine._calculate_source_intelligence(job, apps)
        
        # 5. Team Impact (Step 6)
        team_impact = JobIntelligenceEngine._calculate_team_impact(job, apps)
        
        # 6. Fill Probability / Risk Indicators (Step 7)
        fill_risk = JobIntelligenceEngine._calculate_fill_risk(job, apps, health, velocity)
        
        # 7. Recommended Next Actions
        actions = JobIntelligenceEngine._generate_recommended_actions(job, apps, health, bottlenecks, fill_risk)
        
        return {
            'health': health,
            'velocity': velocity,
            'bottlenecks': bottlenecks,
            'source_intelligence': source_intel,
            'team_impact': team_impact,
            'fill_risk': fill_risk,
            'recommended_actions': actions,
            'summary': {
                'total_candidates': total_apps,
                'active_candidates': apps.exclude(status__in=['joined', 'rejected', 'withdrawn', 'on_hold']).count(),
                'headcount': job.headcount,
                'filled': apps.filter(status='joined').count(),
                'job_age_days': (timezone.now() - job.created_at).days
            }
        }

    @staticmethod
    def _calculate_health(job, apps, velocity, bottlenecks):
        """
        Job Health Model (Step 2)
        Healthy, Watch, At Risk, Critical
        """
        score = 100
        factors = []
        
        # 1. Pipeline Strength (30 points)
        target = job.headcount * 10
        current_count = apps.count()
        if current_count < target:
            penalty = min(30, 30 * (1 - (current_count / target)))
            score -= penalty
            if penalty > 15:
                factors.append({'name': 'Insufficient Pipeline', 'impact': -round(penalty, 1)})
        
        # 2. Overdue Actions (20 points)
        overdue = ActionDeadline.objects.filter(
            entity_type='application',
            entity_id__in=apps.values_list('id', flat=True),
            status='pending',
            deadline_at__lt=timezone.now()
        ).count()
        if overdue > 0:
            penalty = min(20, overdue * 5) # 5 points per overdue
            score -= penalty
            factors.append({'name': 'Overdue Actions', 'impact': -penalty})
            
        # 3. Bottlenecks (20 points)
        if bottlenecks:
            penalty = min(20, len(bottlenecks) * 10)
            score -= penalty
            factors.append({'name': 'Pipeline Bottlenecks', 'impact': -penalty})
            
        # 4. Velocity (30 points)
        if velocity.get('pace_status') == 'Behind':
            score -= 20
            factors.append({'name': 'Slow Movement', 'impact': -20})
        elif velocity.get('pace_status') == 'At Risk':
            score -= 10
            factors.append({'name': 'Pace Warning', 'impact': -10})

        label = 'Healthy'
        if score < 40: label = 'Critical'
        elif score < 60: label = 'At Risk'
        elif score < 85: label = 'Watch'
        
        return {
            'score': round(max(0, score), 1),
            'label': label,
            'factors': factors
        }

    @staticmethod
    def _calculate_velocity(job, apps):
        """
        Hiring Velocity (Step 3)
        """
        history = ApplicationStageHistory.objects.filter(
            application_id__in=apps.values_list('id', flat=True)
        ).values('from_stage_id', 'to_stage_id', 'moved_at', 'application_id')
        
        # Calculate avg time in each stage
        # This is a bit complex to do efficiently in one pass, but let's try a simplified version
        # stage_durations = {} # stage_id -> list of durations
        
        # For simplicity, let's use a heuristic for now: avg time from Applied to Current Status
        now = timezone.now()
        apps_with_duration = apps.annotate(
            duration=now - F('created_at')
        ).exclude(status__in=['joined', 'rejected', 'withdrawn'])
        
        avg_overall_duration = apps_with_duration.aggregate(avg_dur=Avg('duration'))['avg_dur']
        avg_days = avg_overall_duration.days if avg_overall_duration else 0
        
        # Pace calculation
        # If job is 30 days old and we have 0 hires, and target is 1 hire in 45 days.
        target_days = 45 # Default target
        if job.target_date:
            target_days = (job.target_date - job.created_at.date()).days
            
        job_age = (now - job.created_at).days
        filled = apps.filter(status='joined').count()
        
        pace_status = 'On Track'
        if job.headcount > 0:
            progress = filled / job.headcount
            expected_progress = min(1.0, job_age / max(1, target_days))
            if progress < expected_progress * 0.5:
                pace_status = 'Behind'
            elif progress < expected_progress:
                pace_status = 'At Risk'

        # Stage level velocity
        stages = JobStage.objects.filter(requisition_id=job.id).order_by('stage_order')
        stage_velocity = []

        # More accurate duration calculation
        from collections import defaultdict
        stage_durations = defaultdict(list)
        app_history = ApplicationStageHistory.objects.filter(
            application_id__in=apps.values_list('id', flat=True)
        ).order_by('application_id', 'moved_at')

        # Group history by application
        app_histories = defaultdict(list)
        for h in app_history:
            app_histories[h.application_id].append(h)

        for app_id, history_entries in app_histories.items():
            for i in range(len(history_entries) - 1):
                start_history = history_entries[i]
                end_history = history_entries[i+1]
                duration = end_history.moved_at - start_history.moved_at
                if start_history.to_stage_id:
                    stage_durations[start_history.to_stage_id].append(duration.total_seconds())
        
        # Also account for time in current stage for active apps
        active_apps = apps.exclude(status__in=['joined', 'rejected', 'withdrawn'])
        for app in active_apps:
            last_move = ApplicationStageHistory.objects.filter(application_id=app.id).order_by('-moved_at').first()
            if last_move and app.current_stage_id:
                duration = timezone.now() - last_move.moved_at
                stage_durations[app.current_stage_id].append(duration.total_seconds())

        for s in stages:
            durations = stage_durations.get(s.id)
            avg_days = 0
            if durations:
                avg_seconds = sum(durations) / len(durations)
                avg_days = avg_seconds / (24 * 3600)
            
            target_days = s.sla_target_hours / 24
            status = 'Optimal'
            if avg_days > target_days * 1.5:
                status = 'Critical'
            elif avg_days > target_days:
                status = 'Slow'

            stage_velocity.append({
                'stage_id': str(s.id),
                'name': s.name,
                'avg_days': round(avg_days, 1),
                'target_days': target_days,
                'status': status
            })

        return {
            'avg_days_in_pipeline': avg_days,
            'pace_status': pace_status,
            'expected_fill_date': (timezone.now() + timedelta(days=target_days - job_age)).date() if pace_status != 'Behind' else None,
            'stage_velocity': stage_velocity
        }

    @staticmethod
    def _detect_bottlenecks(job, apps):
        """
        Bottleneck Detection (Step 4)
        """
        bottlenecks = []
        total_active = apps.exclude(status__in=['joined', 'rejected', 'withdrawn']).count()
        if total_active == 0:
            return []
            
        # 1. Volume Bottleneck (Too many stuck in one stage)
        stage_counts = apps.exclude(status__in=['joined', 'rejected', 'withdrawn']).values('current_stage_id').annotate(count=Count('id'))
        stages = {str(s.id): s for s in JobStage.objects.filter(requisition_id=job.id)}
        
        for entry in stage_counts:
            raw_sid = entry['current_stage_id']
            count = entry['count']
            if count / total_active > 0.5 and count > 3:
                stage = stages.get(str(raw_sid)) if raw_sid else None
                bottlenecks.append({
                    'type': 'volume',
                    'stage_id': raw_sid,  # Keep as UUID or None, not string "None"
                    'stage_name': stage.name if stage else ('Initial Review' if not raw_sid else 'Unknown'),
                    'severity': 'High',
                    'message': f'50%+ of pipeline ({count} candidates) is stuck here.',
                    'owner_role': stage.responsible_role if stage else 'Recruiter',
                    'suggested_action': 'Batch review or reassignment needed.'
                })
                
        # 2. Conversion Bottleneck (Interviews not converting)
        interviews = Interview.objects.filter(requisition_id=job.id, status='completed')
        if interviews.count() > 5:
            passed = interviews.filter(recommendation='hire').count()
            pass_rate = (passed / interviews.count()) * 100
            if pass_rate < 20:
                bottlenecks.append({
                    'type': 'conversion',
                    'stage_name': 'Interview',
                    'severity': 'Medium',
                    'message': f'Low interview-to-hire conversion rate ({round(pass_rate)}%).',
                    'suggested_action': 'Review interview criteria or sourcing quality.'
                })
        
        # Check offer acceptance rate
        offers_made = apps.filter(offer_date__isnull=False)
        if offers_made.count() > 2: # Only check if a few offers have been made
            offers_accepted = offers_made.filter(offer_accepted_at__isnull=False).count()
            acceptance_rate = (offers_accepted / offers_made.count()) * 100
            if acceptance_rate < 70:
                 bottlenecks.append({
                    'type': 'conversion',
                    'stage_name': 'Offer',
                    'severity': 'High',
                    'message': f'Low offer acceptance rate ({round(acceptance_rate)}%).',
                    'suggested_action': 'Review compensation, benefits, or role clarity.'
                })
                
        # 3. Decision Bottleneck (Pending decisions building up)
        pending_decisions = ActionDeadline.objects.filter(
            entity_type='application',
            entity_id__in=apps.values_list('id', flat=True),
            action_required__icontains='decision',
            status='pending',
            deadline_at__lt=timezone.now()
        ).count()
        if pending_decisions > 3:
            bottlenecks.append({
                'type': 'decision',
                'severity': 'High',
                'message': f'{pending_decisions} pending hiring decisions are overdue.',
                'suggested_action': 'Nudge hiring managers for final decisions.'
            })
            
        return bottlenecks

    @staticmethod
    def _calculate_source_intelligence(job, apps):
        """
        Source Intelligence (Step 5)
        """
        from apps.tenants.models import Client as Agency
        
        sources = apps.values('source', 'agency_id').annotate(
            total=Count('id'),
            qualified=Count('id', filter=Q(status__in=['shortlisted', 'interview', 'assessment', 'offer', 'joined'])),
            hired=Count('id', filter=Q(status='joined'))
        )
        
        source_data = []
        agency_ids = [s['agency_id'] for s in sources if s['agency_id']]
        agencies = {str(a.id): a.name for a in Agency.objects.filter(id__in=agency_ids)}

        for s in sources:
            total = s['total']
            if total == 0: continue
            
            qualified = s['qualified']
            hired = s['hired']
            
            effectiveness = 'Low'
            if hired > 0: effectiveness = 'High'
            elif (qualified / total) > 0.3: effectiveness = 'Medium'

            name = s['source'] or 'Direct'
            if name == 'agency' and s['agency_id']:
                name = f"Agency: {agencies.get(str(s['agency_id']), 'Unknown Agency')}"

            source_data.append({
                'source': name,
                'total_count': total,
                'qualified_count': qualified,
                'hired_count': hired,
                'conversion_rate': round((qualified / total) * 100, 1) if total > 0 else 0,
                'effectiveness': effectiveness
            })
            
        # Grouping to merge any entries that might have the same name after mapping
        from itertools import groupby
        from operator import itemgetter
        
        final_data = []
        source_data.sort(key=itemgetter('source'))
        for key, group in groupby(source_data, key=itemgetter('source')):
            group_list = list(group)
            total = sum(item['total_count'] for item in group_list)
            qualified = sum(item['qualified_count'] for item in group_list)
            hired = sum(item['hired_count'] for item in group_list)

            effectiveness = 'Low'
            if hired > 0: effectiveness = 'High'
            elif (qualified / total) > 0.3: effectiveness = 'Medium'

            final_data.append({
                'source': key,
                'total_count': total,
                'qualified_count': qualified,
                'hired_count': hired,
                'conversion_rate': round((qualified / total) * 100, 1) if total > 0 else 0,
                'effectiveness': effectiveness
            })

        return sorted(final_data, key=lambda x: x['conversion_rate'], reverse=True)

    @staticmethod
    def _calculate_team_impact(job, apps):
        """
        Team Impact (Step 6)
        """
        # Recruiter Load
        recruiter_id = job.recruiter_id
        active_jobs_count = 0
        recruiter_sourced_count = 0
        if recruiter_id:
            active_jobs_count = JobRequisition.objects.filter(recruiter_id=recruiter_id, status='active').count()
            recruiter_sourced_count = apps.filter(submitted_by=recruiter_id).count()
        
        load_impact = 'Low'
        if active_jobs_count > 15: load_impact = 'High'
        elif active_jobs_count > 8: load_impact = 'Medium'
        
        # Hiring Manager Responsiveness
        hm_overdue = 0
        if job.hiring_manager_id:
            hm_overdue = ActionDeadline.objects.filter(
                assigned_to=job.hiring_manager_id,
                status='pending',
                deadline_at__lt=timezone.now()
            ).count()
        
        hm_status = 'Responsive'
        if hm_overdue > 5: hm_status = 'Bottleneck'
        elif hm_overdue > 2: hm_status = 'Slow'
        
        return {
            'recruiter_load': {
                'count': active_jobs_count,
                'impact': load_impact
            },
            'recruiter_contribution': {
                'sourced_by_recruiter': recruiter_sourced_count,
                'sourced_by_others': apps.count() - recruiter_sourced_count
            },
            'hiring_manager_responsiveness': hm_status,
            'hm_overdue_count': hm_overdue,
            'reassignment_suggested': load_impact == 'High' or hm_status == 'Bottleneck'
        }

    @staticmethod
    def _calculate_fill_risk(job, apps, health, velocity):
        """
        Fill Probability / Risk Indicators (Step 7)
        """
        indicators = []
        fill_probability = 80 # Base 80%
        
        if health['label'] == 'Critical':
            fill_probability -= 40
            indicators.append('Critical health score indicates major process failure.')
        elif health['label'] == 'At Risk':
            fill_probability -= 20
            indicators.append('Overall health is trending downwards.')
            
        if velocity['pace_status'] == 'Behind':
            fill_probability -= 20
            indicators.append('Hiring pace is significantly behind schedule.')
            
        if apps.count() < job.headcount * 3:
            fill_probability -= 15
            indicators.append('Extremely thin pipeline for target headcount.')
            
        # Dependence on one source
        sources = apps.values('source').annotate(count=Count('id'))
        if sources.count() == 1 and apps.count() > 5:
            fill_probability -= 10
            indicators.append('High dependency on a single sourcing channel.')

        return {
            'probability': max(5, fill_probability),
            'risk_level': 'High' if fill_probability < 50 else ('Medium' if fill_probability < 75 else 'Low'),
            'indicators': indicators
        }

    @staticmethod
    def _generate_recommended_actions(job, apps, health, bottlenecks, fill_risk):
        """
        Recommended Next Actions
        """
        actions = []
        
        if fill_risk['risk_level'] == 'High':
            actions.append({
                'title': 'Emergency Sourcing Boost',
                'action': 'Enable external agency distribution or increase sourcing budget.',
                'priority': 'High'
            })
            
        for b in bottlenecks:
            if b['type'] == 'decision':
                actions.append({
                    'title': 'Clear Decision Backlog',
                    'action': f'Follow up with {b.get("owner_role", "HM")} on {b.get("message")}',
                    'priority': 'High'
                })
            elif b['type'] == 'volume':
                actions.append({
                    'title': f'Review {b["stage_name"]} backlog',
                    'action': f'Allocate 2 hours to screen {apps.filter(current_stage_id=b["stage_id"]).count()} candidates.',
                    'priority': 'Medium'
                })
                
        if not actions:
            actions.append({
                'title': 'Maintain Momentum',
                'action': 'Review new applications within 24 hours to keep velocity high.',
                'priority': 'Low'
            })
            
        return actions[:3]
