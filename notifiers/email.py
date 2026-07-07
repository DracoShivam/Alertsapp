import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from notifiers.base import BaseNotifier

class EmailNotifier(BaseNotifier):
    def __init__(self, config: dict):
        super().__init__("Email")
        self.config = config
        self.smtp_server = config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = int(config.get("smtp_port", 587))
        self.sender_email = os.environ.get("SMTP_SENDER") or config.get("sender_email")
        self.smtp_user = os.environ.get("SMTP_USER") or self.sender_email
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.recipient_emails = config.get("recipient_emails", [])

    def send_notification(self, jobs: list, source_name: str) -> bool:
        if not self.smtp_password:
            self.logger.warning("SMTP password (env: SMTP_PASSWORD) not configured. Skipping email.")
            return False

        if not self.sender_email or not self.recipient_emails:
            self.logger.warning("Email sender or recipient settings missing. Skipping.")
            return False

        if not jobs:
            return True

        self.logger.info(f"Sending Email notifications for {len(jobs)} jobs from {source_name}")

        # Build premium HTML content
        job_rows = ""
        for job in jobs:
            job_rows += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px 8px; font-weight: 600; color: #1a202c;">
                    <a href="{job['link']}" style="color: #3182ce; text-decoration: none;">{job['title']}</a>
                </td>
                <td style="padding: 12px 8px; color: #4a5568;">{job['department']}</td>
                <td style="padding: 12px 8px; color: #4a5568;">{job['location']}</td>
                <td style="padding: 12px 8px; color: #4a5568;">{job.get('experience', 'Not Specified')}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Job Openings</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f7fafc; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0; overflow: hidden;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">New Job Alert!</h1>
                    <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Found matching positions at <strong>{source_name}</strong></p>
                </div>
                
                <!-- Content -->
                <div style="padding: 24px;">
                    <p style="color: #4a5568; font-size: 16px; line-height: 1.5; margin-top: 0;">
                        Hi there, our automated job tracker bot detected the following new positions:
                    </p>
                    
                    <table style="width: 100%; border-collapse: collapse; text-align: left; margin: 20px 0; font-size: 14px;">
                        <thead>
                            <tr style="border-bottom: 2px solid #cbd5e0; color: #718096; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">
                                <th style="padding: 8px 8px;">Role</th>
                                <th style="padding: 8px 8px;">Department</th>
                                <th style="padding: 8px 8px;">Location</th>
                                <th style="padding: 8px 8px;">Experience</th>
                            </tr>
                        </thead>
                        <tbody>
                            {job_rows}
                        </tbody>
                    </table>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{jobs[0]['link']}" style="background-color: #4f46e5; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; font-size: 14px;">View Postings</a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f7fafc; padding: 16px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #a0aec0;">
                    This is an automated notification from your Job Tracker Bot.
                </div>
            </div>
        </body>
        </html>
        """

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔔 New Job Alert: {len(jobs)} role(s) open at {source_name}"
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipient_emails)

            msg.attach(MIMEText(html_content, "html"))

            # SMTP Connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.sender_email, self.recipient_emails, msg.as_string())
            server.quit()
            
            self.logger.info("Alert email sent successfully.")
            return True
        except Exception as e:
            self.logger.exception(f"Error sending email: {e}")
            return False
