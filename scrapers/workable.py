import re
import requests
from scrapers.base import BaseScraper

class WorkableScraper(BaseScraper):
    def __init__(self):
        super().__init__("Workable")

    def scrape(self, url: str, filters: dict) -> list:
        self.logger.info(f"Starting scrape for Workable careers at {url}")
        try:
            # Extract company slug from URL
            # Handles: https://apply.workable.com/junglee-games/
            #          https://apply.workable.com/lakshyadigitalglobal
            match = re.search(r'apply\.workable\.com/([^/?\s]+)', url)
            if not match:
                self.logger.error(f"Could not extract Workable company slug from URL: {url}")
                return []

            company_slug = match.group(1)
            api_url = f"https://apply.workable.com/api/v3/accounts/{company_slug}/jobs"

            self.logger.info(f"Fetching jobs from Workable API: {api_url}")
            headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

            # Fetch all jobs (API returns up to 10 per call; paginate via nextPage token)
            all_jobs_raw = []
            payload = {}
            while True:
                res = requests.post(api_url, json=payload, headers=headers, timeout=15)
                res.raise_for_status()
                data = res.json()
                results = data.get("results", [])
                all_jobs_raw.extend(results)
                next_page = data.get("nextPage")
                if not next_page:
                    break
                payload = {"nextPage": next_page}

            jobs = []
            for job in all_jobs_raw:
                shortcode = job.get("shortcode")
                job_id = str(job.get("id", shortcode))

                # Build locations string — API returns either a 'locations' list or single 'location' dict
                location_obj = job.get("location")
                locations = job.get("locations", [])
                if locations:
                    loc_parts = []
                    for loc in locations:
                        city = loc.get("city", "")
                        country = loc.get("country", "")
                        loc_parts.append(city if city else country)
                    loc_str = ", ".join(filter(None, loc_parts)) or "Not Specified"
                elif location_obj and isinstance(location_obj, dict):
                    city = location_obj.get("city", "")
                    country = location_obj.get("country", "")
                    loc_str = city if city else (country or "Not Specified")
                elif job.get("remote"):
                    loc_str = "Remote"
                else:
                    loc_str = "Not Specified"

                # Departments are a list
                depts = job.get("department", [])
                dept_str = ", ".join(depts) if depts else "General"

                # Job type mapping
                job_type = job.get("type", "").replace("_", " ").title()

                jobs.append({
                    "id": f"workable-{company_slug}-{job_id}",
                    "title": job.get("title"),
                    "department": dept_str,
                    "location": loc_str,
                    "link": f"https://apply.workable.com/{company_slug}/j/{shortcode}",
                    "experience": "Not Specified",
                    "type": job_type or "Full Time",
                    "source": self.name
                })

            self.logger.info(f"Found {len(jobs)} total jobs on Workable portal for '{company_slug}'")
            filtered_jobs = self._filter_jobs(jobs, filters)
            self.logger.info(f"Filtered to {len(filtered_jobs)} matching jobs")
            return filtered_jobs

        except Exception as e:
            self.logger.exception(f"Error scraping Workable portal {url}: {e}")
            return []
