import re
import requests
from scrapers.base import BaseScraper

class LeverScraper(BaseScraper):
    def __init__(self):
        super().__init__("Lever")

    def scrape(self, url: str, filters: dict) -> list:
        self.logger.info(f"Starting scrape for Lever careers at {url}")
        try:
            # Extract company name from URL
            match = re.search(r'jobs\.lever\.co/([^/]+)', url)
            if not match:
                self.logger.error(f"Could not extract Lever company name from URL: {url}")
                return []
            
            company = match.group(1)
            api_url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            
            self.logger.info(f"Fetching jobs from Lever API: {api_url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(api_url, headers=headers, timeout=15)
            res.raise_for_status()
            raw_jobs = res.json()
            
            jobs = []
            for job in raw_jobs:
                job_id = job.get("id")
                categories = job.get("categories") or {}
                
                dept = categories.get("department") or categories.get("team") or "General"
                loc = categories.get("location") or "Remote"
                commitment = categories.get("commitment") or "Full Time"
                
                jobs.append({
                    "id": f"lever-{company}-{job_id}",
                    "title": job.get("title"),
                    "department": dept,
                    "location": loc,
                    "link": job.get("hostedUrl"),
                    "experience": "Not Specified",
                    "type": commitment,
                    "source": self.name
                })
                
            self.logger.info(f"Found {len(jobs)} total jobs on Lever portal")
            filtered_jobs = self._filter_jobs(jobs, filters)
            self.logger.info(f"Filtered to {len(filtered_jobs)} matching jobs")
            return filtered_jobs
            
        except Exception as e:
            self.logger.exception(f"Error scraping Lever portal {url}: {e}")
            return []
