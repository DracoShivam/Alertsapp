import os
import requests
from notifiers.base import BaseNotifier

class DiscordNotifier(BaseNotifier):
    def __init__(self, config: dict):
        super().__init__("Discord")
        self.config = config
        # Use env var first, then fall back to config
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL") or config.get("webhook_url")

    def send_notification(self, jobs: list, source_name: str) -> bool:
        if not self.webhook_url:
            self.logger.warning("Discord webhook URL not configured. Skipping.")
            return False

        if not jobs:
            return True

        self.logger.info(f"Sending Discord notifications for {len(jobs)} jobs from {source_name}")

        embeds = []
        for job in jobs:
            # Construct a sleek embed card for each job
            embed = {
                "title": f"🆕 {job['title']}",
                "description": f"A new position is open at **{source_name}**.",
                "url": job["link"],
                "color": 3447003,  # Premium dark blue / violet
                "fields": [
                    {"name": "Department", "value": job["department"], "inline": True},
                    {"name": "Location", "value": job["location"], "inline": True},
                    {"name": "Experience", "value": job.get("experience", "Not Specified"), "inline": True},
                ],
                "footer": {
                    "text": f"Source: {job['source']} | Job Tracker Bot",
                }
            }
            if job.get("type"):
                embed["fields"].append({"name": "Job Type", "value": job["type"], "inline": True})
                
            embeds.append(embed)

        # Discord webhooks support up to 10 embeds per message.
        # If we have more than 10, we'll chunk them.
        chunk_size = 10
        success = True
        
        for i in range(0, len(embeds), chunk_size):
            chunk = embeds[i:i + chunk_size]
            payload = {
                "username": "Job Alert Bot",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/3820/3820331.png",
                "embeds": chunk
            }
            
            try:
                res = requests.post(self.webhook_url, json=payload, timeout=15)
                if res.status_code not in (200, 204):
                    self.logger.error(f"Failed to send Discord webhook: {res.status_code} - {res.text}")
                    success = False
            except Exception as e:
                self.logger.exception(f"Error sending Discord webhook: {e}")
                success = False

        return success
