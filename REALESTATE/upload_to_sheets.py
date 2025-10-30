# Upload CSV data to Google Sheets
import sys
import os
import pandas as pd

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'utils'))

from app.utils.logger import logger
from app.utils.config_loader import CONFIG

def upload_csv_to_google_sheets():
    """Upload the generated CSV to Google Sheets"""
    
    csv_path = "./data/classified_listings.csv"
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        logger.error("CSV file not found. Please run generate_csv.py first.")
        return False
    
    # Check credentials
    creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
    if not os.path.exists(creds_path):
        logger.error(f"Google credentials not found at: {creds_path}")
        logger.info("Please follow the setup guide in GOOGLE_SHEETS_SETUP.md")
        
        # Offer alternative: manual CSV upload
        logger.info("ALTERNATIVE: Manual Upload Instructions")
        logger.info("1. Open Google Sheets: https://sheets.google.com/")
        logger.info("2. Create a new spreadsheet")
        logger.info("3. Go to File > Import")
        logger.info("4. Upload your CSV file from: %s", os.path.abspath(csv_path))
        logger.info("5. Choose 'Replace spreadsheet' and click 'Import data'")
        
        return False
    
    try:
        # Import Google Sheets libraries
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Setup credentials
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        logger.info("Authenticating with Google Sheets...")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        sheet_id = CONFIG["GOOGLE_SHEETS_ID"]
        logger.info(f"Opening Google Sheet: {sheet_id}")
        sheet = client.open_by_key(sheet_id)
        
        # Create or get worksheet
        worksheet_name = "Real Estate Listings"
        try:
            worksheet = sheet.worksheet(worksheet_name)
            logger.info(f"Found existing worksheet: {worksheet_name}")
        except:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            logger.info(f"Created new worksheet: {worksheet_name}")
        
        # Read CSV data
        logger.info(f"Reading CSV data from: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Prepare data for upload
        headers = df.columns.tolist()
        data = df.fillna("").values.tolist()
        
        # Upload to Google Sheets
        logger.info("Uploading data to Google Sheets...")
        worksheet.clear()  # Clear existing data
        worksheet.update([headers] + data)  # Upload headers + data
        
        # Format the sheet
        worksheet.format('A1:K1', {
            "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
            "textFormat": {"bold": True}
        })
        
        # Get the sheet URL
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        
        logger.info("✅ SUCCESS! Data uploaded to Google Sheets")
        logger.info(f"📊 Uploaded {len(df)} listings")
        logger.info(f"🔗 Sheet URL: {sheet_url}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error uploading to Google Sheets: %s", e)
        
        # Provide helpful error messages
        if "credentials" in str(e).lower():
            logger.error("❌ Credentials issue - check your google_credentials.json file")
        elif "permission" in str(e).lower():
            logger.error("❌ Permission issue - make sure you shared the sheet with your service account email")
        elif "not found" in str(e).lower():
            logger.error("❌ Sheet not found - check your GOOGLE_SHEETS_ID in .env file")
        
        logger.info("💡 See GOOGLE_SHEETS_SETUP.md for detailed setup instructions")
        return False

def create_sample_google_sheet():
    """Create a sample Google Sheet URL with instructions"""
    
    csv_path = "./data/classified_listings.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        logger.info("🔗 Quick Google Sheets Options:")
        logger.info("1. MANUAL UPLOAD:")
        logger.info("   - Go to: https://sheets.google.com/")
        logger.info("   - Create new sheet > File > Import > Upload CSV")
        logger.info(f"   - Upload file: {os.path.abspath(csv_path)}")
        
        logger.info("2. GOOGLE SHEETS IMPORT FUNCTION:")
        logger.info('   - Create new sheet and use: =IMPORTDATA("URL_TO_YOUR_CSV")')
        
        logger.info("3. AUTOMATED UPLOAD (requires setup):")
        logger.info("   - Follow instructions in GOOGLE_SHEETS_SETUP.md")
        logger.info("   - Then run this script again")
        
        # Show data preview
        logger.info(f"\n📊 Data Preview ({len(df)} rows):")
        print(df.head(3).to_string())

if __name__ == "__main__":
    logger.info("🚀 Starting Google Sheets upload...")
    
    success = upload_csv_to_google_sheets()
    
    if not success:
        logger.info("\n📋 Alternative options available:")
        create_sample_google_sheet()