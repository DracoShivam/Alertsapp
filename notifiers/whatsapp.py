import os
import requests
from notifiers.base import BaseNotifier

class WhatsAppNotifier(BaseNotifier):
    def __init__(self, config: dict):
        super().__init__("WhatsApp")
        self.config = config
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID") or config.get("twilio_account_sid")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN") or config.get("twilio_auth_token")
        self.from_number = os.environ.get("TWILIO_FROM_NUMBER") or config.get("twilio_from_number", "whatsapp:+14155238886")
        self.recipient_number = os.environ.get("TWILIO_TO_NUMBER") or config.get("recipient_number")

    def send_notification(self, jobs: list, source_name: str) -> bool:
        if not self.account_sid or not self.auth_token:
            self.logger.warning("Twilio Account SID or Auth Token missing. Skipping WhatsApp.")
            return False

        if not self.recipient_number:
            self.logger.warning("WhatsApp recipient number not configured. Skipping.")
            return False

        if not jobs:
            return True

        self.logger.info(f"Sending WhatsApp notification for {len(jobs)} jobs from {source_name}")

        # Formulate a clean WhatsApp text message
        body = f"🔔 *Job Alert: {source_name}*\n\n"
        body += f"Found {len(jobs)} new matching job postings:\n\n"
        
        for job in jobs[:5]:  # Limit to 5 in a single text message to avoid truncation/spam filters
            body += f"• *{job['title']}*\n"
            body += f"  Dept: {job['department']}\n"
            body += f"  Loc: {job['location']}\n"
            body += f"  Link: {job['link']}\n\n"

        if len(jobs) > 5:
            body += f"And {len(jobs) - 5} more positions. Check careers website for details!"

        # Ensure the numbers have whatsapp: prefix
        from_num = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"
        to_num = self.recipient_number if self.recipient_number.startswith("whatsapp:") else f"whatsapp:{self.recipient_number}"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        payload = {
            "From": from_num,
            "To": to_num,
            "Body": body
        }

        try:
            res = requests.post(url, data=payload, auth=(self.account_sid, self.auth_token), timeout=15)
            if res.status_code not in (200, 201):
                self.logger.error(f"Failed to send Twilio message: {res.status_code} - {res.text}")
                return False
                
            self.logger.info("WhatsApp notification sent successfully.")
            return True
        except Exception as e:
            self.logger.exception(f"Error sending WhatsApp: {e}")
            return False
