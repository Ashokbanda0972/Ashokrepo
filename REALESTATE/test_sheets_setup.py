# Test Google Sheets connection and upload
import sys
import os
import pandas as pd

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'utils'))

from app.utils.logger import logger
from app.utils.config_loader import CONFIG

def test_google_sheets_setup():
    """Test all aspects of Google Sheets setup"""
    
    logger.info("🧪 Testing Google Sheets Setup...")
    
    # Test 1: Check credentials file
    creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
    logger.info(f"📁 Checking credentials file: {creds_path}")
    
    if not os.path.exists(creds_path):
        logger.error("❌ Credentials file not found!")
        logger.info("💡 Download the JSON key from Google Cloud Console")
        logger.info("💡 Rename it to 'google_credentials.json'")  
        logger.info("💡 Place it in the project root folder")
        return False
    else:
        logger.info("✅ Credentials file found")
        
        # Test credentials content
        try:
            import json
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            if 'client_email' in creds_data:
                logger.info(f"📧 Service account email: {creds_data['client_email']}")
                logger.info("💡 Make sure you shared your Google Sheet with this email!")
            else:
                logger.error("❌ Invalid credentials file format")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error reading credentials: {e}")
            return False
    
    # Test 2: Check Google Sheets libraries
    logger.info("📦 Checking Google Sheets libraries...")
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        logger.info("✅ Google Sheets libraries available")
    except ImportError as e:
        logger.error(f"❌ Missing library: {e}")
        logger.info("💡 Install with: pip install gspread google-auth")
        return False
    
    # Test 3: Test authentication
    logger.info("🔐 Testing Google authentication...")
    try:
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        logger.info("✅ Authentication successful")
        
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        logger.info("💡 Check your credentials file and permissions")
        return False
    
    # Test 4: Test sheet access
    sheet_id = CONFIG["GOOGLE_SHEETS_ID"]
    logger.info(f"📊 Testing sheet access: {sheet_id}")
    
    try:
        sheet = client.open_by_key(sheet_id)
        logger.info(f"✅ Sheet accessed: '{sheet.title}'")
        
        # Try to get or create a worksheet
        try:
            worksheet = sheet.worksheet("Test Connection")
            logger.info("📋 Found existing 'Test Connection' worksheet")
        except:
            worksheet = sheet.add_worksheet(title="Test Connection", rows=10, cols=5)
            logger.info("📋 Created new 'Test Connection' worksheet")
        
        # Test write permission
        worksheet.update('A1', 'Connection Test - ' + str(pd.Timestamp.now()))
        logger.info("✅ Write permission confirmed")
        
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        logger.info(f"🔗 Sheet URL: {sheet_url}")
        
    except Exception as e:
        logger.error(f"❌ Sheet access failed: {e}")
        
        if "not found" in str(e).lower():
            logger.info("💡 Check your GOOGLE_SHEETS_ID in .env file")
        elif "permission" in str(e).lower():
            logger.info("💡 Share your Google Sheet with the service account email")
        
        return False
    
    # Test 5: Full upload test
    logger.info("🚀 Testing full CSV upload...")
    
    csv_path = "./data/classified_listings.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            
            # Upload to test worksheet
            headers = df.columns.tolist()
            data = df.fillna("").values.tolist()
            
            worksheet.clear()
            worksheet.update([headers] + data[:5])  # Upload first 5 rows for test
            
            logger.info(f"✅ Test upload successful ({len(data[:5])} rows)")
            logger.info("🎉 Google Sheets setup is working perfectly!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload test failed: {e}")
            return False
    else:
        logger.warning("⚠️ No CSV file found for upload test")
        logger.info("💡 Run generate_csv.py first to create test data")
        return False

def upload_real_data():
    """Upload the actual CSV data to Google Sheets"""
    
    if not test_google_sheets_setup():
        logger.error("❌ Setup test failed. Please fix issues above.")
        return False
    
    logger.info("📤 Uploading real data to Google Sheets...")
    
    try:
        # Import libraries
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Setup authentication
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open sheet
        sheet_id = CONFIG["GOOGLE_SHEETS_ID"]
        sheet = client.open_by_key(sheet_id)
        
        # Create or get main worksheet
        worksheet_name = "Real Estate Data"
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=15)
        
        # Load and upload CSV
        csv_path = "./data/classified_listings.csv"
        df = pd.read_csv(csv_path)
        
        headers = df.columns.tolist()
        data = df.fillna("").values.tolist()
        
        # Clear and upload
        worksheet.clear()
        worksheet.update([headers] + data)
        
        # Format header row
        worksheet.format('A1:K1', {
            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })
        
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        
        logger.info("🎉 SUCCESS! Data uploaded to Google Sheets")
        logger.info(f"📊 Uploaded {len(df)} real estate listings")
        logger.info(f"🔗 View your data: {sheet_url}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Google Sheets Setup Test & Upload")
    
    # First run setup test
    setup_ok = test_google_sheets_setup()
    
    if setup_ok:
        logger.info("\n" + "="*50)
        logger.info("🚀 Setup test passed! Proceeding with real upload...")
        upload_real_data()
    else:
        logger.info("\n" + "="*50)
        logger.info("❌ Setup test failed. Please follow these steps:")
        logger.info("1. Check AUTOMATED_SHEETS_SETUP.md for detailed instructions")
        logger.info("2. Ensure google_credentials.json is in the right location")
        logger.info("3. Verify your Google Sheet is shared with the service account")
        logger.info("4. Run this test again after fixing issues")