# Playwright-based Zillow scraper (example)
from playwright.sync_api import sync_playwright
from app.utils.config_loader import CONFIG
from app.utils.logger import logger
import time
import re

TARGET_CITY = CONFIG["TARGET_CITY"]
HEADLESS = CONFIG["PLAYWRIGHT_HEADLESS"]

def parse_price(text):
    if not text:
        return None
    s = re.sub(r"[^\d]", "", text)
    return int(s) if s else None

def zillow_search_url(city: str, page_num: int = 1):
    # Basic search URL for city; may need refinement to include filters
    base = "https://www.zillow.com/homes/for_sale/"
    return f"{base}{city.replace(' ', '-')}_rb/{page_num}_p/"

def scrape_zillow(max_pages=2):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()
        for pg in range(1, max_pages+1):
            url = zillow_search_url(TARGET_CITY, pg)
            logger.info("Zillow: navigating to %s", url)
            page.goto(url, timeout=60000)
            time.sleep(2)  # allow JS to render - adjust as needed

            # Listing cards selector (this might change; adjust when necessary)
            cards = page.query_selector_all("article.list-card")
            logger.info("Found %d cards on page %d", len(cards), pg)
            for c in cards:
                try:
                    link = c.query_selector("a.list-card-link")
                    href = link.get_attribute("href") if link else None
                    if href and href.startswith("/b/"):
                        href = "https://www.zillow.com" + href
                    price_text = c.query_selector("div.list-card-price").inner_text() if c.query_selector("div.list-card-price") else None
                    price = parse_price(price_text)
                    address = c.query_selector("address").inner_text() if c.query_selector("address") else None
                    info = c.query_selector(".list-card-details")
                    beds = baths = living_area = None
                    if info:
                        txt = info.inner_text()
                        # parse patterns like "3 bds | 2 ba | 1,500 sqft"
                        m = re.findall(r"([\d,]+)\s*bd|([\d,\.]+)\s*ba|([\d,\,]+)\s*sqft", txt)
                        # simple regex parsing:
                        parts = txt.split(" · ")
                        for part in parts:
                            if "bd" in part:
                                beds = int(re.sub(r"[^\d]", "", part) or 0)
                            if "ba" in part:
                                baths = float(re.sub(r"[^\d\.]", "", part) or 0)
                            if "sqft" in part:
                                living_area = int(re.sub(r"[^\d]", "", part) or 0)
                    results.append({
                        "source": "zillow",
                        "url": href,
                        "address": address,
                        "price": price,
                        "beds": beds,
                        "baths": baths,
                        "living_area": living_area,
                        "raw_json": None
                    })
                except Exception as e:
                    logger.exception("Error parsing a card: %s", e)
        browser.close()
    return results
