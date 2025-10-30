# Simplified and more robust scraper implementations
from playwright.sync_api import sync_playwright
from app.utils.config_loader import CONFIG  
from app.utils.logger import logger
import time
import re
import random

TARGET_CITY = CONFIG["TARGET_CITY"]
HEADLESS = CONFIG["PLAYWRIGHT_HEADLESS"]

def setup_stealth_browser(p):
    """Setup browser with stealth settings"""
    browser = p.chromium.launch(
        headless=HEADLESS,
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    )
    
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    return browser, context

def scrape_zillow_simple():
    """Simplified Zillow scraper with better selectors"""
    results = []
    
    with sync_playwright() as p:
        browser, context = setup_stealth_browser(p)
        page = context.new_page()
        
        try:
            # Use a more direct approach - search for Newton MA properties
            search_url = "https://www.zillow.com/newton-ma/"
            logger.info(f"Accessing Zillow: {search_url}")
            
            page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
            
            # Wait and add random delay
            time.sleep(random.uniform(5, 10))
            
            # Try to find ANY property listings with multiple approaches
            all_selectors = [
                'article[data-zpid]',
                '[data-testid="property-card"]', 
                'div[role="listitem"]',
                '.ListItem-c11n-8-84-3__sc-10e22w8-0',
                '.property-card',
                'article.list-card',
                'div[class*="PropertyCard"]'
            ]
            
            found_listings = []
            for selector in all_selectors:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 2:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    found_listings = elements[:10]  # Limit to first 10
                    break
            
            if not found_listings:
                logger.info("Trying to find any links that might be properties...")
                # Fallback: look for any links that might be properties  
                property_links = page.query_selector_all('a[href*="homedetails"]')
                if property_links:
                    logger.info(f"Found {len(property_links)} property links")
                    
                    for link in property_links[:5]:
                        try:
                            href = link.get_attribute('href')
                            if href:
                                results.append({
                                    "source": "zillow",
                                    "url": f"https://www.zillow.com{href}" if href.startswith('/') else href,
                                    "address": "Address extraction needed",
                                    "price": None,
                                    "beds": None,
                                    "baths": None,
                                    "living_area": None,
                                    "raw_json": {"method": "link_extraction"}
                                })
                        except Exception as e:
                            logger.debug(f"Error processing property link: {e}")
                            continue
            else:
                # Process found listings
                for i, listing in enumerate(found_listings[:5]):
                    try:
                        # Try to extract any text that might be useful
                        text_content = listing.inner_text() if hasattr(listing, 'inner_text') else ""
                        
                        # Look for price patterns in the text
                        price_match = re.search(r'\$[\d,]+', text_content)
                        price_text = price_match.group() if price_match else None
                        
                        # Look for address-like text
                        address_lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        potential_address = None
                        for line in address_lines:
                            if any(word in line.lower() for word in ['st', 'ave', 'rd', 'dr', 'way', 'ct']):
                                potential_address = line
                                break
                        
                        results.append({
                            "source": "zillow",
                            "url": None,
                            "address": potential_address,
                            "price": int(re.sub(r'[^\d]', '', price_text)) if price_text else None,
                            "beds": None,
                            "baths": None, 
                            "living_area": None,
                            "raw_json": {"text_content": text_content[:200], "method": "text_extraction"}
                        })
                        
                    except Exception as e:
                        logger.debug(f"Error processing listing {i}: {e}")
                        continue
                        
        except Exception as e:
            logger.exception(f"Error in Zillow scraping: {e}")
        
        finally:
            browser.close()
    
    logger.info(f"Zillow simple scraper found {len(results)} results")
    return results

def scrape_test_site():
    """Test with a simple property site to verify scraping works"""
    results = []
    
    with sync_playwright() as p:
        browser, context = setup_stealth_browser(p)
        page = context.new_page()
        
        try:
            # Test with a simple real estate site
            test_url = "https://www.homes.com/newton-ma/"
            logger.info(f"Testing with: {test_url}")
            
            page.goto(test_url, timeout=60000)
            time.sleep(5)
            
            # Look for property cards
            cards = page.query_selector_all('.property-card, .listing-card, [class*="property"], [class*="listing"]')
            logger.info(f"Found {len(cards)} potential property elements")
            
            for i, card in enumerate(cards[:3]):
                try:
                    text = card.inner_text()
                    if '$' in text and len(text) > 20:
                        results.append({
                            "source": "homes.com",
                            "url": test_url,
                            "address": "Test address from homes.com",
                            "price": None,
                            "beds": None,
                            "baths": None,
                            "living_area": None,
                            "raw_json": {"text": text[:100]}
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.exception(f"Error testing site: {e}")
            
        finally:
            browser.close()
    
    return results

if __name__ == "__main__":
    logger.info("Testing simplified scrapers...")
    
    # Test the simplified scraper
    zillow_results = scrape_zillow_simple()
    
    # Test with alternative site
    test_results = scrape_test_site()
    
    total = len(zillow_results) + len(test_results)
    logger.info(f"Results - Zillow: {len(zillow_results)}, Test site: {len(test_results)}, Total: {total}")
    
    if zillow_results:
        logger.info(f"Sample Zillow result: {zillow_results[0]}")
    if test_results:
        logger.info(f"Sample test result: {test_results[0]}")