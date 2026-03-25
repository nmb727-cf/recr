from apps.rbac.permissions import require_permission


can_view_email_accounts = require_permission('communication.email_accounts.view')
can_manage_email_accounts = require_permission('communication.email_accounts.manage')
can_view_email_templates = require_permission('communication.email_templates.view')
can_manage_email_templates = require_permission('communication.email_templates.manage')
can_manage_quick_replies = require_permission('communication.quick_replies.manage')
can_send_email = require_permission('communication.email.send')
can_send_shared = require_permission('communication.email.send_from_shared_account')
can_view_email_audit = require_permission('communication.email.audit.view')
