import logging

class BaseScraper:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name.lower().replace(' ', '_')}")

    def scrape(self, url: str, filters: dict) -> list:
        """
        Scrapes a job board URL and returns a list of jobs matching the configured filters.
        
        Args:
            url (str): The career board URL.
            filters (dict): Dictionary of filters (e.g. {'departments': [...], 'title_keywords': [...]}).
            
        Returns:
            list[dict]: A list of job dicts matching the structure:
                {
                    'id': str,
                    'title': str,
                    'department': str,
                    'location': str,
                    'link': str,
                    'experience': str (optional),
                    'type': str (optional),
                    'source': str
                }
        """
        raise NotImplementedError("Scrapers must implement the scrape method.")
        
    def _filter_jobs(self, jobs: list, filters: dict) -> list:
        """
        Helper method to filter jobs by department and title keywords.
        """
        if not filters:
            return jobs
            
        filtered = []
        target_depts = [d.lower() for d in filters.get("departments", []) if d]
        title_keywords = [k.lower() for k in filters.get("title_keywords", []) if k]
        
        for job in jobs:
            # Filter by department if specified
            if target_depts:
                dept = (job.get("department") or "").lower()
                if not any(target in dept for target in target_depts):
                    continue
                    
            # Filter by title keywords if specified
            if title_keywords:
                title = (job.get("title") or "").lower()
                if not any(keyword in title for keyword in title_keywords):
                    continue
                    
            filtered.append(job)
            
        return filtered
