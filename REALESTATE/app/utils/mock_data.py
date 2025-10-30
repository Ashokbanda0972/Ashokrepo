# Mock data generator for testing the pipeline when scraping fails
from app.utils.logger import logger
import random
from datetime import datetime

def generate_mock_listings(source="mock", count=5):
    """Generate realistic mock property listings for testing"""
    
    # Sample addresses in Newton, MA area
    addresses = [
        "123 Commonwealth Ave, Newton, MA 02459",
        "456 Beacon Street, Newton, MA 02468", 
        "789 Washington Street, Newton, MA 02458",
        "321 Centre Street, Newton, MA 02459",
        "654 Walnut Street, Newton, MA 02468",
        "987 Highland Ave, Newton, MA 02461",
        "147 Woodward Street, Newton, MA 02459",
        "258 Parker Street, Newton, MA 02458"
    ]
    
    # Realistic price ranges for Newton area
    price_ranges = [
        (800000, 1200000),  # High-end
        (600000, 900000),   # Mid-range
        (500000, 700000),   # Lower-mid
        (400000, 600000)    # Starter homes
    ]
    
    listings = []
    
    for i in range(count):
        price_range = random.choice(price_ranges)
        price = random.randint(price_range[0], price_range[1])
        
        # Generate realistic property features
        beds = random.choice([2, 3, 3, 4, 4, 5])  # 3-4 bed most common
        baths = random.choice([1.5, 2, 2.5, 3, 3.5]) 
        sqft = random.randint(1200, 3500)
        
        listing = {
            "source": source,
            "url": f"https://example.com/listing-{i+1}",
            "address": random.choice(addresses),
            "price": price,
            "beds": beds,
            "baths": baths,
            "living_area": sqft,
            "raw_json": {
                "generated": True,
                "timestamp": datetime.now().isoformat(),
                "note": f"Mock data generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }
        
        listings.append(listing)
    
    return listings

def scrape_with_fallback(scraper_func, scraper_name, use_mock=True):
    """Run a scraper with fallback to mock data if it fails"""
    try:
        logger.info(f"Attempting to scrape {scraper_name}...")
        results = scraper_func()
        
        if results and len(results) > 0:
            logger.info(f"{scraper_name} successfully found {len(results)} listings")
            return results
        else:
            logger.warning(f"{scraper_name} returned no results")
            
    except Exception as e:
        logger.exception(f"Error in {scraper_name} scraper: %s", e)
    
    # Fallback to mock data if enabled
    if use_mock:
        logger.info(f"Using mock data for {scraper_name}")
        return generate_mock_listings(source=scraper_name.lower(), count=random.randint(2, 5))
    
    return []

if __name__ == "__main__":
    # Test mock data generation
    logger.info("Testing mock data generation...")
    
    mock_zillow = generate_mock_listings("zillow", 3)
    mock_redfin = generate_mock_listings("redfin", 2) 
    mock_realtor = generate_mock_listings("realtor", 4)
    
    total = len(mock_zillow) + len(mock_redfin) + len(mock_realtor)
    logger.info(f"Generated {total} total mock listings")
    logger.info(f"Zillow: {len(mock_zillow)}, Redfin: {len(mock_redfin)}, Realtor: {len(mock_realtor)}")
    
    # Show sample
    if mock_zillow:
        logger.info(f"Sample mock listing: {mock_zillow[0]}")