#!/usr/bin/env python3
"""Test Google Sheets integration with corrected credentials"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

def test_google_sheets_upload():
    """Test uploading data to Google Sheets"""
    load_dotenv()
    
    try:
        # Read the CSV data
        csv_path = "./data/classified_listings.csv"
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return False
            
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows from CSV")
        
        # Set up Google Sheets credentials
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', './google_credentials.json')
        sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        
        if not os.path.exists(credentials_path):
            print(f"❌ Credentials file not found: {credentials_path}")
            return False
            
        print(f"📁 Using credentials: {credentials_path}")
        print(f"📊 Target sheet ID: {sheets_id}")
        
        # Authenticate with Google Sheets
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            credentials_path, 
            scopes=scopes
        )
        
        client = gspread.authorize(credentials)
        print("✅ Google Sheets authentication successful!")
        
        # Open the spreadsheet
        sheet = client.open_by_key(sheets_id)
        worksheet = sheet.sheet1  # Use the first worksheet
        
        print(f"✅ Opened spreadsheet: {sheet.title}")
        
        # Clear existing data and upload new data
        worksheet.clear()
        
        # Convert DataFrame to list of lists for upload
        data_to_upload = [df.columns.tolist()] + df.values.tolist()
        
        # Upload the data
        worksheet.update('A1', data_to_upload)
        
        print(f"🎉 Successfully uploaded {len(df)} rows to Google Sheets!")
        print(f"📊 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{sheets_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Google Sheets Integration...")
    test_google_sheets_upload()