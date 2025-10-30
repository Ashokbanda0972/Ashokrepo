# Google Sheets Setup Guide

## 🔧 Step 1: Create Google Service Account

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create or Select Project**
   - Create a new project or select existing one
   - Name it something like "RealEstate-Scraper"

3. **Enable Google Sheets API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
   - Also enable "Google Drive API"

4. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name: "realestate-sheets-service"
   - Role: "Editor"
   - Click "Create and Continue"

5. **Generate JSON Key**
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Download the file

## 📁 Step 2: Place Credentials File

- Rename the downloaded JSON file to `google_credentials.json`
- Place it in your project root: `C:\Users\Ashok Reddy\Desktop\REALESTATE\`

## 📊 Step 3: Create Google Sheet

1. **Create New Sheet**
   - Go to https://sheets.google.com/
   - Create a new blank spreadsheet
   - Name it "Real Estate Listings"

2. **Share with Service Account**
   - Click "Share" button
   - Add the service account email (found in the JSON file, looks like: `xxxxx@xxxxx.iam.gserviceaccount.com`)
   - Give "Editor" permissions
   - Click "Send"

3. **Copy Sheet ID**
   - From the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Copy the SHEET_ID_HERE part
   - Update your `.env` file with this ID

## ⚙️ Step 4: Update Configuration

Your `.env` file should look like:
```
GOOGLE_CREDENTIALS_PATH=./google_credentials.json
GOOGLE_SHEETS_ID=YOUR_ACTUAL_SHEET_ID_HERE
```

## 🚀 Step 5: Test Upload

Run the upload script to send your CSV data to Google Sheets!