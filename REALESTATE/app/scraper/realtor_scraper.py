# Updated Realtor.com scraper with Playwright and current selectors  
from playwright.sync_api import sync_playwright
from app.utils.config_loader import CONFIG
from app.utils.logger import logger
import time
import re
import random
import urllib.parse

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

def build_realtor_search_url(city: str, state: str = None):
    """Build Realtor.com search URL"""
    # Parse city and state from TARGET_CITY if it contains comma
    if ',' in city:
        city_part, state_part = city.split(',', 1)
        city_clean = city_part.strip()
        state_clean = state_part.strip()
    else:
        city_clean = city.strip()
        state_clean = state or "MA"  # Default to MA if no state provided
    
    # URL encode the search parameters
    city_encoded = urllib.parse.quote_plus(city_clean)
    state_encoded = urllib.parse.quote_plus(state_clean)
    
    # Realtor.com search URL format
    base_url = "https://www.realtor.com/realestateandhomes-search"
    return f"{base_url}/{city_encoded}_{state_encoded}"

def setup_browser_context(browser):
    """Setup browser context with realistic headers"""
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    return context

def scrape_realtor(max_pages=1):
    """
    Scrape Realtor.com for property listings
    Note: Realtor.com is heavily protected and may require additional anti-detection measures
    """
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = setup_browser_context(browser)
        page = context.new_page()
        
        # Set additional headers to avoid detection
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
        })
        
        try:
            # Navigate to Realtor.com search results
            url = build_realtor_search_url(TARGET_CITY)
            logger.info("Realtor.com: navigating to %s", url)
            
            # Navigate with extended timeout
            page.goto(url, timeout=90000, wait_until='networkidle')
            time.sleep(random.uniform(4, 8))
            
            # Handle potential bot detection or cookie consent
            try:
                # Look for cookie consent buttons
                cookie_selectors = ['button[aria-label*="Accept"]', 'button[id*="cookie"]', 'button[class*="consent"]']
                for selector in cookie_selectors:
                    element = page.query_selector(selector)
                    if element:
                        element.click()
                        time.sleep(1)
                        break
            except:
                pass
            
            # Wait for listings to appear
            time.sleep(random.uniform(3, 6))
            
            # Try multiple selectors for property cards
            card_selectors = [
                '[data-testid="property-card"]',
                '.BasePropertyCard',
                '[data-rf-test-name="PropertyCard"]',
                '.property-card-primary',
                '.card-content',
                '[class*="PropertyCard"]'
            ]
            
            cards = []
            for selector in card_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    cards = page.query_selector_all(selector)
                    if cards:
                        logger.info(f"Found {len(cards)} Realtor.com cards using selector: {selector}")
                        break
                except:
                    continue
            
            if not cards:
                # Fallback: try generic selectors
                generic_selectors = ['[class*="card"]', '[class*="listing"]', '[class*="property"]']
                for selector in generic_selectors:
                    cards = page.query_selector_all(selector)
                    if len(cards) > 5:  # Only if we find a reasonable number
                        logger.info(f"Using fallback selector {selector}, found {len(cards)} elements")
                        break
            
            if not cards:
                logger.warning("No property cards found on Realtor.com")
                return results
            
            # Process each card
            for i, card in enumerate(cards[:15]):  # Limit to avoid detection
                try:
                    # Extract price
                    price_text = None
                    price_selectors = [
                        '[data-testid="card-price"]',
                        '.price-display',
                        '.card-price',
                        '[class*="price"]'
                    ]
                    
                    for selector in price_selectors:
                        element = card.query_selector(selector)
                        if element:
                            price_text = element.inner_text().strip()
                            if '$' in price_text:  # Ensure it looks like a price
                                break
                    
                    # Extract address
                    address = None
                    address_selectors = [
                        '[data-testid="card-address"]',
                        '.card-address', 
                        '.property-address',
                        '[class*="address"]'
                    ]
                    
                    for selector in address_selectors:
                        element = card.query_selector(selector)
                        if element:
                            address = element.inner_text().strip()
                            # Skip if it doesn't look like an address
                            if len(address) > 10 and ('St' in address or 'Ave' in address or 'Rd' in address or 'Dr' in address or address.count(' ') >= 2):
                                break
                    
                    # Extract URL
                    href = None
                    link_element = card.query_selector('a[href*="/realestateandhomes-detail/"]') or card.query_selector('a')
                    if link_element:
                        href = link_element.get_attribute('href')
                        if href and href.startswith('/'):
                            href = "https://www.realtor.com" + href
                    
                    # Extract property details (beds, baths, sqft)
                    beds = baths = living_area = None
                    
                    detail_selectors = [
                        '[data-testid="property-meta"]',
                        '.card-meta',
                        '.property-meta',
                        '.card-details'
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
                    
                    # Only add listings with meaningful data
                    if (price_text and '$' in price_text) or (address and len(address) > 10):
                        results.append({
                            "source": "realtor",
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
                    logger.exception(f"Error parsing Realtor.com card {i}: %s", e)
                    continue
        
        except Exception as e:
            logger.exception("Error during Realtor.com scraping: %s", e)
        
        finally:
            browser.close()
    
    logger.info(f"Realtor.com scraping completed. Found {len(results)} listings")
    return results
