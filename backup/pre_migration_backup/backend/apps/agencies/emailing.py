from apps.communications.services import EmailRoutingService


def send_agency_invite_email(*, recipient_email: str, sender_name: str, portal_name: str, portal_type: str, invite_link: str, user_id=None, tenant_id=None):
    """Send standardized agency/client guest portal invite email."""
    subject = f"You're invited to TalentOS ({portal_type.replace('_', ' ').title()})"
    body_text = (
        f"Hi,\n\n"
        f"{sender_name or 'Someone'} has invited you to access the {portal_type} portal for {portal_name}.\n\n"
        f"Accept invite: {invite_link}\n"
        f"This link expires in 7 days.\n\n"
        f"If you were not expecting this invite, you can ignore this email."
    )

    EmailRoutingService.send_email(
        subject=subject,
        body_text=body_text,
        body_html=None,
        recipient_list=[recipient_email],
        user_id=user_id,
        tenant_id=tenant_id,
    )
