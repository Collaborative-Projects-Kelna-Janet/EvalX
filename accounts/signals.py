from django.db.models.signals import post_save, post_delete
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


# @receiver(post_save, sender=Team)
# def notify_team_on_registration(sender, instance, created, **kwargs):
#     if created:
#         subject = 'Welcome to EVALX - Registration Successful'
#         html_content = f'<p>Hello,</p><p>Your team has been successfully registered.<br>Team ID: {instance.team_id}</p><p>You can now log in to the portal.</p>'
#         recipient_list = [instance.user.email] if hasattr(instance, 'user') and instance.user else []
#         
#         if recipient_list:
#             if send_brevo_email(subject, html_content, recipient_list):
#                 print(f"✅ Success: Email sent to {recipient_list}")
#             else:
#                 print(f"❌ Email Error for Team {instance.team_id}")


@receiver(post_save, sender=Team)
def notify_title_approval(sender, instance, created, **kwargs):
    if not created and instance.is_approved:
        subject = f"Project Title Approved: {instance.project_title}"
        html_content = (
            f"<p>Hello Team {instance.team_id},</p>"
            f"<p>Your project title <strong>'{instance.project_title}'</strong> has been officially APPROVED.</p>"
            f"<p>You can now proceed with your documentation.</p>"
        )
        # Safely extract emails directly from members
        recipient_list = [m.email for m in instance.members.all() if getattr(m, 'email', None)]
        
        if recipient_list:
            if send_brevo_email(subject, html_content, recipient_list):
                print(f"✅ Approval Email sent to Team {instance.team_id}")
            else:
                print(f"❌ Approval Email failed for Team {instance.team_id}")


@receiver(post_save, sender=DocumentSlot)
def notify_deadline_or_review(sender, instance, created, **kwargs):
    # This fires when a Coordinator updates a slot's deadline or review date
    subject = f"Schedule Updated: {instance.title}"
    
    # Helper to handle the 'str' vs 'date' object issue
    def get_date_str(date_val):
        if not date_val:
            return None
        if isinstance(date_val, str):
            try:
                return datetime.strptime(date_val, '%Y-%m-%d').strftime('%d %B, %Y')
            except:
                return date_val
        return date_val.strftime('%d %B, %Y')

    d_str = get_date_str(instance.deadline)
    r_str = get_date_str(instance.review_date)

    # Logic to customize message based on what was updated
    if r_str and d_str:
        body = f"Review Date: {r_str}<br>Submission Deadline: {d_str}"
    elif r_str:
        body = f"Review Date has been set for: {r_str}"
    else:
        body = f"Submission Deadline set for: {d_str}"

    html_content = f"<p>Important Update for {instance.title}:</p><p>{body}</p><p>Please check your dashboard for details.</p>"
    
    # Send to ALL active teams safely
    recipient_list = list(Team.objects.exclude(user__email='').values_list('user__email', flat=True))
    
    if recipient_list:
        if send_brevo_email(subject, html_content, recipient_list):
            print(f"✅ Bulk Notification sent for {instance.title}")
        else:
            print(f"❌ Email failed for {instance.title}")


@receiver(post_delete, sender=DocumentSlot)
def notify_on_deadline_deletion(sender, instance, **kwargs):
    """Fires an email to all teams when a coordinator removes a deadline or review date."""
    subject = f"Schedule Removed: {instance.title}"
    
    html_content = (
        f"<p>Notice: The schedule for <strong>'{instance.title}'</strong> has been removed by the Coordinator.</p>"
        f"<p>Please check your dashboard for further updates or contact your guide for more information.</p>"
    )
    
    # Send to all registered teams safely
    recipient_list = list(Team.objects.exclude(user__email='').values_list('user__email', flat=True))
    
    if recipient_list:
        if send_brevo_email(subject, html_content, recipient_list):
            print(f"⚠️ Deletion Notification sent for {instance.title}")
        else:
            print(f"❌ Deletion Email Error for {instance.title}")