from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Team, DocumentSlot
from datetime import datetime
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def send_brevo_email(subject, html_content, recipient_emails):
    """Dispatches emails via Brevo HTTPS API instead of SMTP sockets."""
    api_key = os.getenv('BREVO_API_KEY')
    if not api_key:
        print("BREVO_API_KEY environment variable missing.")
        return False

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender_email = os.getenv('DEFAULT_FROM_EMAIL', 'cseprojectsaisat@gmail.com')
    sender = {"name": "EvalX System", "email": sender_email}
    to = [{"email": email} for email in recipient_emails if email]

    if not to:
        return False

    send_smail = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        api_instance.send_transac_email(send_smail)
        return True
    except ApiException as e:
        print(f"Brevo API Error: {e}")
        return False


@receiver(post_save, sender=Team)
def notify_title_approval(sender, instance, created, **kwargs):
    if not created and instance.is_approved:
        subject = f"Project Title Approved: {instance.project_title}"
        html_content = (
            f"<p>Hello Team {instance.team_id},</p>"
            f"<p>Your project title <strong>'{instance.project_title}'</strong> has been officially APPROVED.</p>"
            f"<p>You can now proceed with your documentation.</p>"
        )
        
        recipient_list = []

        # 1. Check primary team user email
        if getattr(instance, 'user', None) and getattr(instance.user, 'email', None):
            recipient_list.append(instance.user.email)

        # 2. Check team member emails (handles both m.user.email and m.email)
        for member in instance.members.all():
            if hasattr(member, 'user') and getattr(member.user, 'email', None):
                recipient_list.append(member.user.email)
            elif getattr(member, 'email', None):
                recipient_list.append(member.email)

        # Remove duplicate emails and empty values
        recipient_list = list(set(filter(None, recipient_list)))

        if recipient_list:
            if send_brevo_email(subject, html_content, recipient_list):
                print(f"✅ Approval Email sent to Team {instance.team_id}: {recipient_list}")
            else:
                print(f"❌ Approval Email failed for Team {instance.team_id}")
        else:
            print(f"⚠️ No valid email addresses found for Team {instance.team_id}")

@receiver(post_save, sender=DocumentSlot)
def notify_review(sender, instance, created, **kwargs):
    """Fires ONLY when a Review Date is set or updated for a presentation/review slot."""
    # Check if a review date exists for this slot
    if not instance.review_date:
        return

    subject = f"Review Schedule Updated: {instance.title}"
    
    # Format review date string cleanly
    clean_val = str(instance.review_date).split('T')[0]
    try:
        r_str = datetime.strptime(clean_val, '%Y-%m-%d').strftime('%d %B, %Y')
    except ValueError:
        r_str = clean_val

    html_content = (
        f"<p>Important Update for {instance.title}:</p>"
        f"<p>Review Date has been set for: <strong>{r_str}</strong></p>"
        f"<p>Please check your dashboard for details.</p>"
    )
    
    recipient_list = list(Team.objects.exclude(user__email='').values_list('user__email', flat=True))
    
    if recipient_list:
        if send_brevo_email(subject, html_content, recipient_list):
            print(f"✅ Review Date Notification sent for {instance.title}")
        else:
            print(f"❌ Review Date Email failed for {instance.title}")