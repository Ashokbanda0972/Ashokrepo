# Simple CSV output script - bypasses Google Sheets and OpenAI to focus on data export
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'utils'))

from app.utils.logger import logger
from app.scraper.zillow_scraper import scrape_zillow
from app.scraper.redfin_scraper import scrape_redfin
from app.scraper.realtor_scraper import scrape_realtor
from app.utils.mock_data import scrape_with_fallback, generate_mock_listings
from app.integrations.database_manager import init_db, upsert_listing
import pandas as pd
import json
from datetime import datetime
import os

def simple_classify_listing(listing_data):
    """Simple classification without OpenAI API"""
    price = listing_data.get('price', 0)
    beds = listing_data.get('beds', 0) 
    
    # Simple rule-based classification
    if price and price > 800000:
        if beds and beds >= 4:
            return "luxury-family"
        else:
            return "luxury-condo"
    elif price and price > 500000:
        return "mid-range"
    else:
        return "starter-home"

def simple_score_listing(listing_data):
    """Simple scoring without complex algorithms"""
    score = 0
    
    # Price factor (normalized)
    price = listing_data.get('price', 0)
    if price:
        score += min(price / 1000000 * 50, 50)  # Max 50 points for price
    
    # Bedroom factor
    beds = listing_data.get('beds', 0)
    if beds:
        score += min(beds * 5, 20)  # Max 20 points for bedrooms
    
    # Square footage factor
    sqft = listing_data.get('living_area', 0)
    if sqft:
        score += min(sqft / 100, 30)  # Max 30 points for square footage
    
    return round(score, 2)

def run_csv_pipeline():
    """Run a simplified pipeline focused on CSV output"""
    logger.info("Starting CSV-focused pipeline")
    
    # Create data directory
    os.makedirs("./data", exist_ok=True)
    
    # Initialize database
    init_db()
    
    all_listings = []
    
    # 1) Get listings (with fallback to mock data)
    logger.info("Getting listings from all sources...")
    z_results = scrape_with_fallback(lambda: scrape_zillow(max_pages=1), "Zillow", use_mock=True)
    r_results = scrape_with_fallback(scrape_redfin, "Redfin", use_mock=True)  
    rl_results = scrape_with_fallback(scrape_realtor, "Realtor", use_mock=True)
    
    all_results = z_results + r_results + rl_results
    logger.info("Scraped total %d listings", len(all_results))
    
    # 2) Process each listing
    for i, listing in enumerate(all_results):
        try:
            # Simple classification
            listing["classified_label"] = simple_classify_listing(listing)
            
            # Simple scoring
            listing["score"] = simple_score_listing(listing)
            
            # Ensure raw_json is a string for database storage
            raw_json = listing.get("raw_json", {})
            if isinstance(raw_json, dict):
                listing["raw_json"] = json.dumps(raw_json)
            else:
                listing["raw_json"] = str(raw_json) if raw_json else ""
            
            # Add processing timestamp
            listing["processed_at"] = datetime.utcnow().isoformat()
            
            # Save to database
            upsert_listing(listing)
            
            all_listings.append(listing)
            
            logger.info(f"Processed listing {i+1}/{len(all_results)}: {listing.get('address', 'Unknown address')}")
            
        except Exception as e:
            logger.exception(f"Error processing listing {i}: %s", e)
            continue
    
    # 3) Export to CSV
    if all_listings:
        df = pd.DataFrame(all_listings)
        csv_path = "./data/classified_listings.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(all_listings)} listings to {csv_path}")
        
        # Show summary
        logger.info("CSV Export Summary:")
        logger.info(f"Total listings: {len(all_listings)}")
        logger.info(f"Sources: Zillow: {len(z_results)}, Redfin: {len(r_results)}, Realtor: {len(rl_results)}")
        
        # Show classification breakdown
        classifications = df['classified_label'].value_counts()
        logger.info(f"Classifications: {classifications.to_dict()}")
        
        # Show price range
        prices = df['price'].dropna()
        if len(prices) > 0:
            logger.info(f"Price range: ${prices.min():,.0f} - ${prices.max():,.0f}")
            logger.info(f"Average price: ${prices.mean():,.0f}")
        
        return csv_path
    else:
        logger.warning("No listings to export")
        return None

if __name__ == "__main__":
    csv_file = run_csv_pipeline()
    if csv_file:
        logger.info(f"CSV file generated successfully: {csv_file}")
        
        # Show first few rows as preview
        try:
            df = pd.read_csv(csv_file)
            logger.info("CSV Preview (first 3 rows):")
            print(df.head(3).to_string())
        except Exception as e:
            logger.exception(f"Error reading CSV preview: %s", e)
    else:
        logger.error("Failed to generate CSV file")