import hashlib
from bs4 import BeautifulSoup
import requests
from scrapers.base import BaseScraper

class GenericHtmlScraper(BaseScraper):
    def __init__(self):
        super().__init__("GenericHtml")

    def scrape(self, url: str, filters: dict, selectors: dict = None) -> list:
        self.logger.info(f"Starting generic HTML scrape for {url}")
        if not selectors:
            self.logger.error("No selectors provided for generic HTML scraper.")
            return []

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            
            container_sel = selectors.get("job_container")
            title_sel = selectors.get("title")
            dept_sel = selectors.get("department")
            loc_sel = selectors.get("location")
            link_sel = selectors.get("link")
            
            if not container_sel:
                self.logger.error("Missing 'job_container' selector.")
                return []
                
            containers = soup.select(container_sel)
            self.logger.info(f"Found {len(containers)} job containers using selector '{container_sel}'")
            
            jobs = []
            for item in containers:
                # Extract Title
                title = "Unknown Title"
                if title_sel:
                    title_elem = item.select_one(title_sel)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                # Extract Department
                dept = "General"
                if dept_sel:
                    dept_elem = item.select_one(dept_sel)
                    if dept_elem:
                        dept = dept_elem.get_text(strip=True)
                        
                # Extract Location
                loc = "Remote"
                if loc_sel:
                    loc_elem = item.select_one(loc_sel)
                    if loc_elem:
                        loc = loc_elem.get_text(strip=True)
                        
                # Extract Link
                link = url
                if link_sel:
                    link_elem = item.select_one(link_sel)
                    if link_elem:
                        href = link_elem.get("href")
                        if href:
                            # Handle relative URLs
                            if href.startswith("/"):
                                from urllib.parse import urljoin
                                link = urljoin(url, href)
                            else:
                                link = href
                elif item.name == 'a' and item.get('href'):
                    # If container itself is a link
                    href = item.get('href')
                    if href.startswith("/"):
                        from urllib.parse import urljoin
                        link = urljoin(url, href)
                    else:
                        link = href

                # Generate a stable ID based on title, department, and location
                raw_id_string = f"{title}-{dept}-{loc}".encode('utf-8')
                job_id = hashlib.md5(raw_id_string).hexdigest()
                
                jobs.append({
                    "id": f"generic-{job_id}",
                    "title": title,
                    "department": dept,
                    "location": loc,
                    "link": link,
                    "experience": "Not Specified",
                    "type": "Not Specified",
                    "source": self.name
                })
                
            self.logger.info(f"Found {len(jobs)} total jobs on page")
            filtered_jobs = self._filter_jobs(jobs, filters)
            self.logger.info(f"Filtered to {len(filtered_jobs)} matching jobs")
            return filtered_jobs
            
        except Exception as e:
            self.logger.exception(f"Error scraping generic HTML page {url}: {e}")
            return []
