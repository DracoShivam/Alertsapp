import logging

class BaseNotifier:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"notifier.{name.lower()}")

    def send_notification(self, jobs: list, source_name: str) -> bool:
        """
        Sends notifications for a list of new job postings found for a specific source.
        
        Args:
            jobs (list[dict]): List of job dictionaries.
            source_name (str): Human-readable name of the career board source.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        raise NotImplementedError("Notifiers must implement the send_notification method.")
