# Google Sheets Diagnostic and Fix Script
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'utils'))

from app.utils.logger import logger
from app.utils.config_loader import CONFIG
import json

def diagnose_and_fix_sheets():
    """Diagnose Google Sheets issues and provide specific fixes"""
    
    print("=" * 60)
    print("GOOGLE SHEETS DIAGNOSTIC & FIX TOOL")
    print("=" * 60)
    
    # Check credentials
    creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
    sheet_id = CONFIG["GOOGLE_SHEETS_ID"]
    
    print(f"Credentials file: {creds_path}")
    print(f"Sheet ID: {sheet_id}")
    
    if not os.path.exists(creds_path):
        print("❌ ERROR: Credentials file not found")
        return False
    
    # Read service account email
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        service_email = creds_data.get('client_email')
        project_id = creds_data.get('project_id')
        
        print(f"✅ Service Account Email: {service_email}")
        print(f"✅ Project ID: {project_id}")
        
    except Exception as e:
        print(f"❌ ERROR reading credentials: {e}")
        return False
    
    # Test Google Sheets access
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        print("\n🔐 Testing Google authentication...")
        
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        print("✅ Authentication successful")
        
        # Test sheet access
        print(f"\n📊 Testing access to sheet: {sheet_id}")
        
        try:
            sheet = client.open_by_key(sheet_id)
            print(f"✅ SUCCESS: Accessed sheet '{sheet.title}'")
            
            # Test worksheet creation/access
            try:
                worksheet = sheet.worksheet("Test Worksheet")
                print("✅ Found existing test worksheet")
            except:
                worksheet = sheet.add_worksheet(title="Test Worksheet", rows=10, cols=5)
                print("✅ Created new test worksheet")
            
            # Test write
            worksheet.update('A1', f'Test - {json.dumps({"timestamp": str(pd.Timestamp.now())})}')
            print("✅ Write test successful")
            
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            
            print("\n" + "=" * 60)
            print("🎉 SUCCESS! Google Sheets is working correctly!")
            print(f"📊 Sheet Title: {sheet.title}")
            print(f"🔗 Sheet URL: {sheet_url}")
            print("=" * 60)
            
            return True
            
        except Exception as sheet_error:
            print(f"❌ SHEET ACCESS ERROR: {sheet_error}")
            
            # Provide specific fix instructions
            print("\n🔧 HOW TO FIX:")
            print("1. Open your Google Sheet:")
            print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}")
            print("\n2. Click the 'Share' button (top-right)")
            print("\n3. Add this email address:")
            print(f"   {service_email}")
            print("\n4. Set permission to 'Editor'")
            print("\n5. Click 'Send' (do NOT require sign-in)")
            print("\n6. Run this script again to test")
            
            return False
            
    except ImportError:
        print("❌ ERROR: Missing Google Sheets libraries")
        print("🔧 FIX: Run this command:")
        print("pip install gspread google-auth")
        return False
        
    except Exception as auth_error:
        print(f"❌ AUTHENTICATION ERROR: {auth_error}")
        print("🔧 Check your credentials file and try again")
        return False

def create_new_test_sheet():
    """Create a brand new Google Sheet for testing"""
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
        
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        service_email = creds_data.get('client_email')
        
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        print("\n🆕 Creating a new test Google Sheet...")
        
        # Create new spreadsheet
        sheet = client.create("Real Estate Test Sheet")
        
        # Share with service account (automatic since we created it)
        print(f"✅ Created new sheet: '{sheet.title}'")
        
        new_sheet_id = sheet.id
        sheet_url = f"https://docs.google.com/spreadsheets/d/{new_sheet_id}"
        
        print(f"🆔 New Sheet ID: {new_sheet_id}")
        print(f"🔗 New Sheet URL: {sheet_url}")
        
        # Update .env file with new sheet ID
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Replace the GOOGLE_SHEETS_ID
            new_content = env_content.replace(
                f"GOOGLE_SHEETS_ID={CONFIG['GOOGLE_SHEETS_ID']}", 
                f"GOOGLE_SHEETS_ID={new_sheet_id}"
            )
            
            with open(env_path, 'w') as f:
                f.write(new_content)
            
            print(f"✅ Updated .env file with new Sheet ID")
        
        # Test the new sheet
        worksheet = sheet.sheet1
        worksheet.update('A1', 'Real Estate Data')
        worksheet.update('A2', 'Test successful!')
        
        print("\n🎉 NEW SHEET READY!")
        print(f"📊 Access it here: {sheet_url}")
        print("💡 You can now run the pipeline and it will upload to this sheet")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR creating new sheet: {e}")
        return False

if __name__ == "__main__":
    import pandas as pd
    
    print("🔍 RUNNING DIAGNOSTIC...")
    
    success = diagnose_and_fix_sheets()
    
    if not success:
        print("\n" + "=" * 60)
        print("ALTERNATIVE: CREATE NEW SHEET")
        print("=" * 60)
        
        user_input = input("\nWould you like me to create a new Google Sheet? (y/n): ").lower().strip()
        
        if user_input in ['y', 'yes']:
            create_new_test_sheet()
        else:
            print("\n💡 Please follow the fix instructions above and run this again.")
    
    print("\n🏁 Diagnostic complete!")