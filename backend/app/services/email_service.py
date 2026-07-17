import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.FROM_EMAIL, to, msg.as_string())


def send_invite_email(to_email: str, to_name: str, invite_link: str) -> None:
    subject = "You've been invited as a Team Admin — WinWin Law MLM"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;color:#1e293b;">
      <h2 style="color:#f59e0b;margin-bottom:8px;">Welcome to WinWin Law MLM</h2>
      <p>Hi {to_name},</p>
      <p>You've been invited to join as a <strong>Team Admin</strong>.
         Click the button below to set your password and activate your account.
         This link expires in <strong>48 hours</strong>.</p>
      <div style="margin:32px 0;">
        <a href="{invite_link}"
           style="background:#f59e0b;color:#1e293b;padding:12px 28px;border-radius:8px;
                  font-weight:700;text-decoration:none;display:inline-block;">
          Set Password &amp; Activate
        </a>
      </div>
      <p style="color:#64748b;font-size:13px;">
        Or copy this link:<br/>
        <a href="{invite_link}" style="color:#f59e0b;">{invite_link}</a>
      </p>
      <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;"/>
      <p style="color:#94a3b8;font-size:12px;">
        If you didn't expect this invitation, you can safely ignore this email.
      </p>
    </div>
    """

    if not settings.SMTP_HOST:
        # No SMTP configured — log the link so it's not lost during dev/testing
        logger.warning("SMTP not configured. Invite link for %s: %s", to_email, invite_link)
        return

    try:
        _send_smtp(to_email, subject, html)
        logger.info("Invite email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send invite email to %s", to_email)
        raise
