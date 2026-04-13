from django.core.management.base import BaseCommand
from apps.communications.services import EmailRoutingService
from apps.accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Send a test email using EmailRoutingService'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email')
        parser.add_argument('--user-id', type=str, help='Sender user UUID')
        parser.add_argument('--system', action='store_true', help='Force system email')

    def handle(self, *args, **options):
        recipient = options['email']
        user_id = options['user_id']
        email_type = 'system' if options['system'] else 'user'
        
        user = None
        if user_id:
            user = CustomUser.objects.filter(id=user_id).first()
            if not user:
                self.stderr.write(f"User with ID {user_id} not found.")
                return

        self.stdout.write(f"Sending {email_type} email to {recipient}...")
        
        success = EmailRoutingService.send_email(
            subject="TalentOS Test Email",
            body_text="This is a test email from TalentOS EmailRoutingService.",
            body_html="<p>This is a <b>test email</b> from TalentOS EmailRoutingService.</p>",
            recipient_list=[recipient],
            user_id=user.id if user else None,
            email_type=email_type
        )
        
        if success:
            self.stdout.write(self.style.SUCCESS(f"Successfully sent email to {recipient}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to send email to {recipient}"))
