import hashlib
import re
import requests
import xml.etree.ElementTree as ET
from scrapers.base import BaseScraper

class ZohoRssScraper(BaseScraper):
    """
    Scraper for Zoho Recruit career portals that expose an RSS feed.
    Zoho portals typically have an /rss endpoint; department information is
    usually embedded in the description or job title, so title_keyword
    filtering is the recommended approach.
    """
    def __init__(self):
        super().__init__("ZohoRSS")

    def scrape(self, url: str, filters: dict) -> list:
        # Derive the RSS URL from the base career page URL
        rss_url = url.rstrip("/") + "/rss"
        self.logger.info(f"Fetching Zoho RSS feed from: {rss_url}")

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(rss_url, headers=headers, timeout=15)
            res.raise_for_status()

            root = ET.fromstring(res.text)
            channel = root.find("channel")
            if channel is None:
                self.logger.error("RSS feed has no <channel> element.")
                return []

            items = channel.findall("item")
            self.logger.info(f"Found {len(items)} jobs in Zoho RSS feed")

            jobs = []
            for item in items:
                title_tag = item.find("title")
                link_tag = item.find("link")
                desc_tag = item.find("description")

                title = title_tag.text.strip() if (title_tag is not None and title_tag.text) else "Unknown"
                link = link_tag.text.strip() if (link_tag is not None and link_tag.text) else url
                desc_raw = desc_tag.text or "" if desc_tag is not None else ""

                # Strip HTML tags for extraction
                desc_clean = re.sub(r"<[^>]+>", " ", desc_raw)

                # Extract Category and Location — only the short value (before next field or line break)
                # Use the RAW HTML description to search before stripping, since <br> acts as a delimiter
                cat_match = re.search(r"Category:\s*([^<\n\r]{1,60})", desc_raw)
                loc_match = re.search(r"Location:\s*([^<\n\r]{1,80})", desc_raw)

                category = cat_match.group(1).strip() if cat_match else "General"
                location = loc_match.group(1).strip() if loc_match else "Not Specified"
                # Clean up any leftover HTML entities
                location = re.sub(r"&[a-z]+;", " ", location).strip()

                # Stable ID based on the link (strip RSS source param for cleanliness)
                clean_link = re.sub(r"\?source=RSS", "", link)
                job_id = hashlib.md5(clean_link.encode()).hexdigest()

                jobs.append({
                    "id": f"zoho-{job_id}",
                    "title": title,
                    "department": category,
                    "location": location,
                    "link": clean_link,
                    "experience": "Not Specified",
                    "type": "Full Time",
                    "source": self.name
                })

            filtered_jobs = self._filter_jobs(jobs, filters)
            self.logger.info(f"Filtered to {len(filtered_jobs)} matching jobs")
            return filtered_jobs

        except Exception as e:
            self.logger.exception(f"Error scraping Zoho RSS at {rss_url}: {e}")
            return []
