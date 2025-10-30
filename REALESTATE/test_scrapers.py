# Test script to debug individual scrapers
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'utils'))

from app.utils.logger import logger
from app.scraper.zillow_scraper import scrape_zillow
from app.scraper.redfin_scraper import scrape_redfin
from app.scraper.realtor_scraper import scrape_realtor

def test_individual_scraper(scraper_func, name):
    """Test an individual scraper and report results"""
    logger.info(f"Testing {name} scraper...")
    try:
        results = scraper_func(max_pages=1)
        logger.info(f"{name} returned {len(results)} listings")
        
        if results:
            # Show first result as example
            first_result = results[0]
            logger.info(f"Sample {name} listing: {first_result}")
        
        return results
    except Exception as e:
        logger.exception(f"Error testing {name}: %s", e)
        return []

if __name__ == "__main__":
    logger.info("Starting scraper tests...")
    
    # Test each scraper individually
    zillow_results = test_individual_scraper(scrape_zillow, "Zillow")
    redfin_results = test_individual_scraper(scrape_redfin, "Redfin") 
    realtor_results = test_individual_scraper(scrape_realtor, "Realtor")
    
    # Summary
    total_listings = len(zillow_results) + len(redfin_results) + len(realtor_results)
    logger.info(f"Total listings found: {total_listings}")
    logger.info(f"Zillow: {len(zillow_results)}, Redfin: {len(redfin_results)}, Realtor: {len(realtor_results)}")