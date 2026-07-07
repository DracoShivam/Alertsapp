import re
import requests
from scrapers.base import BaseScraper

class GreenhouseScraper(BaseScraper):
    def __init__(self):
        super().__init__("Greenhouse")

    def scrape(self, url: str, filters: dict) -> list:
        self.logger.info(f"Starting scrape for Greenhouse careers at {url}")
        try:
            # Extract company name from URL
            match = re.search(r'boards\.greenhouse\.io/([^/]+)', url)
            if not match:
                self.logger.error(f"Could not extract Greenhouse company name from URL: {url}")
                return []
            
            company = match.group(1)
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
            
            self.logger.info(f"Fetching jobs from Greenhouse API: {api_url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(api_url, headers=headers, timeout=15)
            res.raise_for_status()
            data = res.json()
            raw_jobs = data.get("jobs", [])
            
            jobs = []
            for job in raw_jobs:
                job_id = str(job.get("id"))
                
                # Extract department name(s)
                depts = [d.get("name") for d in job.get("departments", []) if d.get("name")]
                dept_str = ", ".join(depts) if depts else "General"
                
                loc = job.get("location", {}).get("name") or "Remote"
                
                jobs.append({
                    "id": f"greenhouse-{company}-{job_id}",
                    "title": job.get("title"),
                    "department": dept_str,
                    "location": loc,
                    "link": job.get("absolute_url"),
                    "experience": "Not Specified",
                    "type": "Full Time",  # Greenhouse doesn't expose commitment directly in lists usually
                    "source": self.name
                })
                
            self.logger.info(f"Found {len(jobs)} total jobs on Greenhouse portal")
            filtered_jobs = self._filter_jobs(jobs, filters)
            self.logger.info(f"Filtered to {len(filtered_jobs)} matching jobs")
            return filtered_jobs
            
        except Exception as e:
            self.logger.exception(f"Error scraping Greenhouse portal {url}: {e}")
            return []
