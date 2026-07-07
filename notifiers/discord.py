import os
import requests
from notifiers.base import BaseNotifier

class DiscordNotifier(BaseNotifier):
    def __init__(self, config: dict):
        super().__init__("Discord")
        self.config = config
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL") or config.get("webhook_url")

    def _safe(self, val, fallback="N/A") -> str:
        """Sanitize field values — Discord rejects empty strings."""
        return str(val).strip() or fallback

    def send_notification(self, jobs: list, source_name: str) -> bool:
        if not self.webhook_url:
            self.logger.warning("Discord webhook URL not configured. Skipping.")
            return False

        if not jobs:
            return True

        self.logger.info(f"Sending Discord notifications for {len(jobs)} jobs from {source_name}")

        embeds = []
        for job in jobs:
            embed = {
                "title": f"\U0001f195 {self._safe(job.get('title'))}",
                "description": f"New opening at **{source_name}**",
                "url": job.get("link") or "https://discord.com",
                "color": 5793266,  # Purple/violet
                "fields": [
                    {"name": "Department", "value": self._safe(job.get("department")), "inline": True},
                    {"name": "Location",   "value": self._safe(job.get("location")),   "inline": True},
                    {"name": "Experience", "value": self._safe(job.get("experience")), "inline": True},
                    {"name": "Job Type",   "value": self._safe(job.get("type")),       "inline": True},
                ],
                "footer": {
                    "text": f"Source: {self._safe(job.get('source'))} | Job Tracker Bot"
                }
            }
            embeds.append(embed)

        # Discord supports max 10 embeds per webhook message
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
                else:
                    self.logger.info(f"Sent batch of {len(chunk)} embeds to Discord")
            except Exception as e:
                self.logger.exception(f"Error sending Discord webhook: {e}")
                success = False

        return success
