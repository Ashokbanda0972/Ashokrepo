# Updated Redfin scraper with Playwright and current selectors
from playwright.sync_api import sync_playwright
from app.utils.config_loader import CONFIG
from app.utils.logger import logger
import time
import re
import random
import json

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
    match = re.search(r'([\d,\.]+)', text.replace(',', ''))
    if match:
        try:
            return float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
        except ValueError:
            return default
    return default

def build_redfin_search_url(city: str, page_num: int = 1):
    """Build Redfin search URL for a given city"""
    # Redfin uses a different URL structure - we'll search for the city first
    city_formatted = city.replace(' ', '-').replace(',', '').lower()
    # Start with a basic city search
    base_url = f"https://www.redfin.com/city/{city_formatted}"
    return base_url

def setup_browser_context(browser):
    """Setup browser context with realistic headers to avoid detection"""
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    return context

def scrape_redfin(max_pages=2):
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = setup_browser_context(browser)
        page = context.new_page()
        
        # Set additional headers
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
        })
        
        try:
            # First, navigate to Redfin and search for the city
            logger.info("Redfin: Starting search for %s", TARGET_CITY)
            page.goto("https://www.redfin.com/", timeout=60000)
            time.sleep(random.uniform(2, 4))
            
            # Try to use the search box
            search_selectors = [
                'input[data-rf-test-id="search-box-input"]',
                'input[placeholder*="search"]',
                'input#search-box-input',
                '.search-input-box input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            if search_input:
                # Clear and type the city name
                search_input.fill("")  # Use fill instead of clear for Playwright
                search_input.type(TARGET_CITY, delay=100)
                time.sleep(2)
                
                # Press Enter or click search
                page.keyboard.press('Enter')
                time.sleep(3)
            else:
                # Fallback: try direct URL navigation
                url = build_redfin_search_url(TARGET_CITY)
                logger.info("Redfin: Direct navigation to %s", url)
                page.goto(url, timeout=60000)
            
            # Wait for listings to load
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(random.uniform(3, 6))
            
            # Look for listing containers with multiple selectors
            listing_selectors = [
                '[data-rf-test-id="mapListViewListingCard"]',
                '.HomeCard',
                '.listingCard',
                '.SearchResultsGrid .listingCard',
                '[class*="HomeCard"]'
            ]
            
            listings = []
            for selector in listing_selectors:
                try:
                    listings = page.query_selector_all(selector)
                    if listings:
                        logger.info(f"Found {len(listings)} Redfin listings using selector: {selector}")
                        break
                except:
                    continue
            
            if not listings:
                logger.warning("No Redfin listings found with any selector")
                return results
            
            for i, listing in enumerate(listings[:20]):  # Limit to avoid being detected
                try:
                    # Extract price
                    price_text = None
                    price_selectors = [
                        '[data-rf-test-id="listingCard-price"]',
                        '.homecardV2Price',
                        '.price',
                        '[class*="price"]'
                    ]
                    
                    for selector in price_selectors:
                        element = listing.query_selector(selector)
                        if element:
                            price_text = element.inner_text().strip()
                            break
                    
                    # Extract address
                    address = None
                    address_selectors = [
                        '[data-rf-test-id="listingCard-address"]',
                        '.homecardV2Address',
                        '.address',
                        '[class*="address"]'
                    ]
                    
                    for selector in address_selectors:
                        element = listing.query_selector(selector)
                        if element:
                            address = element.inner_text().strip()
                            break
                    
                    # Extract URL
                    href = None
                    link_element = listing.query_selector('a[href*="/home/"]') or listing.query_selector('a')
                    if link_element:
                        href = link_element.get_attribute('href')
                        if href and href.startswith('/'):
                            href = "https://www.redfin.com" + href
                    
                    # Extract property details
                    beds = baths = living_area = None
                    
                    # Look for beds/baths/sqft info
                    stats_selectors = [
                        '[data-rf-test-id="listingCard-stats"]',
                        '.homecardV2Stats',
                        '.stats',
                        '.HomeStatsV2'
                    ]
                    
                    for selector in stats_selectors:
                        stats_element = listing.query_selector(selector)
                        if stats_element:
                            stats_text = stats_element.inner_text()
                            
                            # Parse beds
                            bed_match = re.search(r'(\d+)\s*(?:bed|bd)', stats_text, re.IGNORECASE)
                            if bed_match:
                                beds = int(bed_match.group(1))
                            
                            # Parse baths  
                            bath_match = re.search(r'([\d\.]+)\s*(?:bath|ba)', stats_text, re.IGNORECASE)
                            if bath_match:
                                baths = float(bath_match.group(1))
                            
                            # Parse square footage
                            sqft_match = re.search(r'([\d,]+)\s*(?:sqft|sq\.?\s*ft)', stats_text, re.IGNORECASE)
                            if sqft_match:
                                living_area = int(sqft_match.group(1).replace(',', ''))
                            
                            break
                    
                    # Only add if we have meaningful data
                    if price_text or address:
                        results.append({
                            "source": "redfin",
                            "url": href,
                            "address": address,
                            "price": parse_price(price_text),
                            "beds": beds,
                            "baths": baths,
                            "living_area": living_area,
                            "raw_json": {
                                "price_text": price_text,
                                "listing_index": i
                            }
                        })
                
                except Exception as e:
                    logger.exception(f"Error parsing Redfin listing {i}: %s", e)
                    continue
        
        except Exception as e:
            logger.exception("Error during Redfin scraping: %s", e)
        
        finally:
            browser.close()
    
    logger.info(f"Redfin scraping completed. Found {len(results)} listings")
    return results
