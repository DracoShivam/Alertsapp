import re
import requests
from urllib.parse import urlparse
from scrapers.base import BaseScraper

class KekaScraper(BaseScraper):
    def __init__(self):
        super().__init__("Keka")

    def scrape(self, url: str, filters: dict) -> list:
        self.logger.info(f"Starting scrape for Keka careers at {url}")
        try:
            # 1. Fetch the landing page
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            html = res.text

            # 2. Extract the portal identifier
            identifier = None
            # Match method 1: /ats/documents/<uuid>/
            match = re.search(r'/ats/documents/([a-f0-9\-]+)/', html)
            if match:
                identifier = match.group(1)
            else:
                # Match method 2: embedjobs/js/<uuid>
                match = re.search(r'embedjobs/js/([a-f0-9\-]+)', html)
                if match:
                    identifier = match.group(1)
                else:
                    # Match method 3: identifier: '<uuid>'
                    match = re.search(r'identifier\s*:\s*[\'"]([a-f0-9\-]+)[\'"]', html)
                    if match:
                        identifier = match.group(1)

            if not identifier:
                self.logger.error(f"Could not extract Keka portal identifier from {url}")
                return []

            self.logger.info(f"Extracted portal identifier: {identifier}")

            # 3. Fetch jobs from the active API
            parsed = urlparse(url)
            api_url = f"{parsed.scheme}://{parsed.netloc}/careers/api/embedjobs/default/active/{identifier}"
            
            self.logger.info(f"Fetching job listings from API: {api_url}")
            api_res = requests.get(api_url, headers=headers, timeout=15)
            api_res.raise_for_status()
            raw_jobs = api_res.json()

            # 4. Map raw jobs to standard format
            jobs = []
            base_url = url.rstrip('/')
            
            for job in raw_jobs:
                job_id = str(job.get("id"))
                locations = [loc.get("name") for loc in job.get("jobLocations", []) if loc.get("name")]
                location_str = ", ".join(locations) if locations else "Remote"
                
                # jobType mapping: Keka typically uses numbers: 1 = Intern, 2 = Full-time, etc.
                job_type_val = job.get("jobType")
                job_type_str = "Full Time" if job_type_val == 2 else "Contract/Other"
                
                jobs.append({
                    "id": f"keka-{identifier}-{job_id}",
                    "title": job.get("title"),
                    "department": job.get("departmentName") or "General",
                    "location": location_str,
                    "link": f"{base_url}/job/{job_id}",
                    "experience": job.get("experience") or "Not Specified",
                    "type": job_type_str,
                    "source": self.name
                })

            self.logger.info(f"Found {len(jobs)} total jobs on Keka portal")
            
            # 5. Filter the jobs
            filtered_jobs = self._filter_jobs(jobs, filters)
            self.logger.info(f"Filtered to {len(filtered_jobs)} matching jobs")
            return filtered_jobs

        except Exception as e:
            self.logger.exception(f"Error scraping Keka portal {url}: {e}")
            return []
