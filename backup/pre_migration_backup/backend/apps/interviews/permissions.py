"""
RBAC permission constants for the Interviews module.

Permission code format: <module>.<resource>.<action>

Usage:
    from apps.interviews.permissions import can_view_interviews

    class InterviewListView(APIView):
        permission_classes = [IsAuthenticated, can_view_interviews]
"""
from apps.rbac.permissions import require_permission

# ─── Interview Types (catalog) ─────────────────────────────────────────────────
can_view_interview_types   = require_permission('interviews.type.view')
can_manage_interview_types = require_permission('interviews.type.manage')

# ─── Interview Templates ───────────────────────────────────────────────────────
can_view_templates   = require_permission('interviews.template.view')
can_create_templates = require_permission('interviews.template.create')
can_edit_templates   = require_permission('interviews.template.edit')
can_delete_templates = require_permission('interviews.template.delete')

# ─── Interviews ────────────────────────────────────────────────────────────────
can_view_interviews   = require_permission('interviews.interview.view')
can_create_interviews = require_permission('interviews.interview.create')
can_edit_interviews   = require_permission('interviews.interview.edit')
can_delete_interviews = require_permission('interviews.interview.delete')
can_start_interview   = require_permission('interviews.interview.start')
can_complete_interview = require_permission('interviews.interview.complete')
can_cancel_interview  = require_permission('interviews.interview.cancel')

# ─── Panelists ─────────────────────────────────────────────────────────────────
can_manage_panelists = require_permission('interviews.panelist.manage')

# ─── Feedback ──────────────────────────────────────────────────────────────────
can_submit_feedback = require_permission('interviews.feedback.submit')
can_view_feedback   = require_permission('interviews.feedback.view')

# ─── Decision ──────────────────────────────────────────────────────────────────
can_record_decision = require_permission('interviews.decision.record')
can_view_decision   = require_permission('interviews.decision.view')
