from scrapers.keka import KekaScraper
from scrapers.lever import LeverScraper
from scrapers.greenhouse import GreenhouseScraper
from scrapers.generic_html import GenericHtmlScraper
from scrapers.workable import WorkableScraper
from scrapers.zoho_rss import ZohoRssScraper

SCRAPERS = {
    "keka": KekaScraper,
    "lever": LeverScraper,
    "greenhouse": GreenhouseScraper,
    "generic_html": GenericHtmlScraper,
    "workable": WorkableScraper,
    "zoho_rss": ZohoRssScraper
}

def get_scraper(scraper_type: str):
    """
    Returns the scraper class matching the given type.
    """
    scraper_class = SCRAPERS.get(scraper_type.lower())
    if not scraper_class:
        raise ValueError(f"Unknown scraper type: {scraper_type}. Available types: {list(SCRAPERS.keys())}")
    return scraper_class()
