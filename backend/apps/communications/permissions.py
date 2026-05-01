from apps.rbac.permissions import require_permission
from shared.actor_access import require_non_candidate, require_tenant_or_platform_admin


# Notification Control Center
can_view_notification_rules    = require_permission('communication.notification_rules.view')
can_manage_notification_rules  = require_permission('communication.notification_rules.manage')

can_view_email_accounts = require_permission('communication.email_accounts.view')
can_manage_email_accounts = require_permission('communication.email_accounts.manage')
can_view_email_templates = require_permission('communication.email_templates.view')
can_manage_email_templates = require_permission('communication.email_templates.manage')
can_manage_quick_replies = require_permission('communication.quick_replies.manage')
can_send_email = require_permission('communication.email.send')
can_send_shared = require_permission('communication.email.send_from_shared_account')
can_view_email_audit = require_permission('communication.email.audit.view')


def require_internal_communications_actor(user):
    require_non_candidate(
        user,
        'You do not have permission to manage internal communication operations.',
    )


def require_communications_admin_actor(user):
    require_tenant_or_platform_admin(
        user,
        'Admin access required for this communication operation.',
    )
