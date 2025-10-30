# Updated Zillow scraper with current website selectors and anti-detection measures
from playwright.sync_api import sync_playwright
from app.utils.config_loader import CONFIG
from app.utils.logger import logger
import time
import re
import random

TARGET_CITY = CONFIG["TARGET_CITY"]
HEADLESS = CONFIG["PLAYWRIGHT_HEADLESS"]

def parse_price(text):
    if not text:
        return None
    # Remove all non-digits and convert to int
    s = re.sub(r"[^\d]", "", text)
    return int(s) if s else None

def parse_number(text, default=None):
    if not text:
        return default
    # Extract numbers including decimals
    match = re.search(r'([\d,\.]+)', text.replace(',', ''))
    if match:
        try:
            return float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
        except ValueError:
            return default
    return default

def zillow_search_url(city: str, page_num: int = 1):
    # Updated Zillow search URL format for for-sale properties
    city_formatted = city.replace(' ', '-').replace(',', '').lower()
    # Use for-sale search which is more reliable
    base_url = f"https://www.zillow.com/{city_formatted}"
    if page_num == 1:
        return f"{base_url}/"
    else:
        return f"{base_url}/{page_num}_p/"

def setup_browser_context(browser):
    """Setup browser context with realistic headers and settings"""
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    return context

def scrape_zillow(max_pages=2):
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = setup_browser_context(browser)
        page = context.new_page()
        
        # Set additional headers to look more like a real browser
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Upgrade-Insecure-Requests': '1',
        })
        
        for pg in range(1, max_pages + 1):
            try:
                url = zillow_search_url(TARGET_CITY, pg)
                logger.info("Zillow: navigating to %s", url)
                
                # Navigate with longer timeout and wait for network idle
                page.goto(url, timeout=90000, wait_until='networkidle')
                
                # Random delay to avoid detection
                time.sleep(random.uniform(3, 7))
                
                # Wait for listings to load - try multiple possible selectors
                selectors_to_try = [
                    '[data-testid="property-card"]',
                    'article[data-zpid]',
                    '.ListItem-c11n-8-84-3__sc-10e22w8-0',
                    '.list-card-wrapper',
                    '[role="listitem"]'
                ]
                
                cards = []
                for selector in selectors_to_try:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        cards = page.query_selector_all(selector)
                        if cards:
                            logger.info(f"Found {len(cards)} cards using selector: {selector}")
                            break
                    except:
                        continue
                
                if not cards:
                    logger.warning(f"No listings found on page {pg} with any selector")
                    continue
                
                logger.info("Found %d listings on page %d", len(cards), pg)
                
                for i, card in enumerate(cards):
                    try:
                        # Extract price with multiple selectors
                        price_text = None
                        price_selectors = [
                            '[data-testid="property-card-price"]',
                            '.PropertyCardWrapper__StyledPriceLine',
                            '.list-card-price',
                            '.price'
                        ]
                        
                        for selector in price_selectors:
                            element = card.query_selector(selector)
                            if element:
                                price_text = element.inner_text().strip()
                                break
                        
                        # Extract address
                        address = None
                        address_selectors = [
                            '[data-testid="property-card-addr"]',
                            'address',
                            '.list-card-addr',
                            '.StyledPropertyCardDataArea-address'
                        ]
                        
                        for selector in address_selectors:
                            element = card.query_selector(selector)
                            if element:
                                address = element.inner_text().strip()
                                break
                        
                        # Extract URL/link
                        href = None
                        link_selectors = ['a[href*="/homedetails/"]', 'a[href*="/b/"]', 'a']
                        
                        for selector in link_selectors:
                            element = card.query_selector(selector)
                            if element:
                                href = element.get_attribute("href")
                                if href:
                                    if href.startswith('/'):
                                        href = "https://www.zillow.com" + href
                                    break
                        
                        # Extract property details (beds, baths, sqft)
                        beds = baths = living_area = None
                        
                        detail_selectors = [
                            '[data-testid="property-card-details"]',
                            '.list-card-details',
                            '.PropertyCardWrapper__StyledPropertyCardDataArea'
                        ]
                        
                        for selector in detail_selectors:
                            details_element = card.query_selector(selector)
                            if details_element:
                                details_text = details_element.inner_text()
                                
                                # Parse beds
                                bed_match = re.search(r'(\d+)\s*(?:bed|bd)', details_text, re.IGNORECASE)
                                if bed_match:
                                    beds = int(bed_match.group(1))
                                
                                # Parse baths
                                bath_match = re.search(r'([\d\.]+)\s*(?:bath|ba)', details_text, re.IGNORECASE)
                                if bath_match:
                                    baths = float(bath_match.group(1))
                                
                                # Parse square footage
                                sqft_match = re.search(r'([\d,]+)\s*(?:sqft|sq\.?\s*ft)', details_text, re.IGNORECASE)
                                if sqft_match:
                                    living_area = int(sqft_match.group(1).replace(',', ''))
                                
                                break
                        
                        # Only add if we have at least a price or address
                        if price_text or address:
                            results.append({
                                "source": "zillow",
                                "url": href,
                                "address": address,
                                "price": parse_price(price_text),
                                "beds": beds,
                                "baths": baths,
                                "living_area": living_area,
                                "raw_json": {
                                    "price_text": price_text,
                                    "page_number": pg,
                                    "card_index": i
                                }
                            })
                            
                    except Exception as e:
                        logger.exception(f"Error parsing card {i} on page {pg}: %s", e)
                        continue
                
                # Random delay between pages
                if pg < max_pages:
                    time.sleep(random.uniform(2, 5))
                    
            except Exception as e:
                logger.exception(f"Error scraping Zillow page {pg}: %s", e)
                continue
        
        browser.close()
    
    logger.info(f"Zillow scraping completed. Found {len(results)} total listings")
    return results
