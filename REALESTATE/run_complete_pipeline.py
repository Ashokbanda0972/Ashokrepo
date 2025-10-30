# Complete pipeline: Generate CSV and upload to Google Sheets
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'utils'))

from app.utils.logger import logger
from app.scraper.zillow_scraper import scrape_zillow
from app.scraper.redfin_scraper import scrape_redfin
from app.scraper.realtor_scraper import scrape_realtor
from app.utils.mock_data import scrape_with_fallback
from app.integrations.database_manager import init_db, upsert_listing
from app.utils.config_loader import CONFIG
import pandas as pd
import json
from datetime import datetime

def simple_classify_listing(listing_data):
    """Simple classification without OpenAI API"""
    price = listing_data.get('price', 0)
    beds = listing_data.get('beds', 0) 
    
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
    
    price = listing_data.get('price', 0)
    if price:
        score += min(price / 1000000 * 50, 50)
    
    beds = listing_data.get('beds', 0)
    if beds:
        score += min(beds * 5, 20)
    
    sqft = listing_data.get('living_area', 0)
    if sqft:
        score += min(sqft / 100, 30)
    
    return round(score, 2)

def upload_to_google_sheets(df):
    """Upload DataFrame to Google Sheets"""
    
    creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
    if not os.path.exists(creds_path):
        logger.warning("Google credentials not found - skipping Sheets upload")
        logger.info("💡 To enable Google Sheets: follow AUTOMATED_SHEETS_SETUP.md")
        return False
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Setup authentication
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        logger.info("🔐 Authenticating with Google Sheets...")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        sheet_id = CONFIG["GOOGLE_SHEETS_ID"]
        sheet = client.open_by_key(sheet_id)
        
        # Create or get worksheet
        worksheet_name = f"Real Estate Data - {datetime.now().strftime('%Y-%m-%d')}"
        try:
            worksheet = sheet.worksheet(worksheet_name)
            logger.info(f"📋 Using existing worksheet: {worksheet_name}")
        except:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=15)
            logger.info(f"📋 Created new worksheet: {worksheet_name}")
        
        # Prepare data
        headers = df.columns.tolist()
        data = df.fillna("").values.tolist()
        
        # Upload to Google Sheets
        logger.info("📤 Uploading data to Google Sheets...")
        worksheet.clear()
        worksheet.update([headers] + data)
        
        # Format header row
        worksheet.format('A1:K1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
        
        # Add summary info
        summary_row = len(data) + 3
        worksheet.update(f'A{summary_row}', f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        worksheet.update(f'A{summary_row + 1}', f'Total Listings: {len(data)}')
        
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        
        logger.info("✅ SUCCESS! Data uploaded to Google Sheets")
        logger.info(f"📊 Uploaded {len(data)} listings")
        logger.info(f"🔗 View online: {sheet_url}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Google Sheets upload failed: {e}")
        
        if "credentials" in str(e).lower():
            logger.info("💡 Check your google_credentials.json file")
        elif "permission" in str(e).lower():
            logger.info("💡 Share your Google Sheet with the service account email")
        elif "not found" in str(e).lower():
            logger.info("💡 Check your GOOGLE_SHEETS_ID in .env file")
            
        return False

def run_complete_pipeline():
    """Run the complete pipeline: scrape, process, save CSV, upload to Sheets"""
    
    logger.info("🚀 Starting Complete Real Estate Pipeline")
    
    # Create directories
    os.makedirs("./data", exist_ok=True)
    
    # Initialize database
    init_db()
    
    # 1) Scrape data from all sources
    logger.info("🕷️ Scraping real estate data...")
    z_results = scrape_with_fallback(lambda: scrape_zillow(max_pages=1), "Zillow", use_mock=True)
    r_results = scrape_with_fallback(scrape_redfin, "Redfin", use_mock=True)  
    rl_results = scrape_with_fallback(scrape_realtor, "Realtor", use_mock=True)
    
    all_results = z_results + r_results + rl_results
    logger.info(f"📊 Found {len(all_results)} total listings")
    
    # 2) Process each listing
    processed_listings = []
    
    for i, listing in enumerate(all_results):
        try:
            # Classification and scoring
            listing["classified_label"] = simple_classify_listing(listing)
            listing["score"] = simple_score_listing(listing)
            
            # Prepare raw_json for database
            raw_json = listing.get("raw_json", {})
            if isinstance(raw_json, dict):
                listing["raw_json"] = json.dumps(raw_json)
            else:
                listing["raw_json"] = str(raw_json) if raw_json else ""
            
            # Add timestamps - use current local time
            listing["processed_at"] = datetime.now().isoformat()
            
            # Save to database
            upsert_listing(listing)
            processed_listings.append(listing)
            
            logger.info(f"✅ Processed {i+1}/{len(all_results)}: {listing.get('address', 'Unknown')}")
            
        except Exception as e:
            logger.exception(f"❌ Error processing listing {i}: %s", e)
            continue
    
    if not processed_listings:
        logger.error("❌ No listings were successfully processed")
        return False
    
    # 3) Create DataFrame for export
    df = pd.DataFrame(processed_listings)
    
    # 4) Save CSV
    csv_path = "./data/classified_listings.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"💾 Saved CSV: {csv_path}")
    
    # 5) Upload to Google Sheets
    sheets_success = upload_to_google_sheets(df)
    
    # 6) Show summary
    logger.info("\n" + "="*50)
    logger.info("🎉 PIPELINE COMPLETE!")
    logger.info(f"📊 Total listings processed: {len(processed_listings)}")
    logger.info(f"🏠 Sources: Zillow({len(z_results)}), Redfin({len(r_results)}), Realtor({len(rl_results)})")
    
    # Show classifications
    classifications = df['classified_label'].value_counts()
    logger.info(f"🏷️ Classifications: {classifications.to_dict()}")
    
    # Show price stats
    prices = df['price'].dropna()
    if len(prices) > 0:
        logger.info(f"💰 Price range: ${prices.min():,.0f} - ${prices.max():,.0f}")
        logger.info(f"💰 Average: ${prices.mean():,.0f}")
    
    # Output locations
    logger.info(f"📁 CSV file: {os.path.abspath(csv_path)}")
    if sheets_success:
        logger.info("📊 Google Sheets: Successfully uploaded")
    else:
        logger.info("📊 Google Sheets: Not configured (see AUTOMATED_SHEETS_SETUP.md)")
    
    return True

if __name__ == "__main__":
    success = run_complete_pipeline()
    
    if success:
        logger.info("\n✅ All done! Your real estate data is ready for analysis.")
    else:
        logger.error("\n❌ Pipeline failed. Check logs above for details.")