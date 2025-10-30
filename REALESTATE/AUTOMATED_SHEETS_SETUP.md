# Automated Google Sheets Setup - Step by Step

## 🔧 Step 1: Google Cloud Console

### A. Create Google Cloud Project
1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. Click "New Project" (top-left, next to "Google Cloud")
4. Project Name: "RealEstate-Scraper" 
5. Click "Create"

### B. Enable Required APIs
1. In your project, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API" → Click it → Click "Enable"
3. Search for "Google Drive API" → Click it → Click "Enable"

### C. Create Service Account
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Service account name: "realestate-sheets"
4. Service account ID: (auto-generated)
5. Click "Create and Continue"
6. Role: Select "Editor"
7. Click "Continue" > "Done"

### D. Generate JSON Key
1. In "Credentials", click on your service account email
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Choose "JSON" format
5. Click "Create" - file will download automatically
6. **IMPORTANT**: Rename this file to `google_credentials.json`

## 📁 Step 2: Place Credentials File

1. Move the downloaded `google_credentials.json` to:
   `C:\Users\Ashok Reddy\Desktop\REALESTATE\`

2. The file should be in the same folder as your `generate_csv.py`

## 📊 Step 3: Create Google Sheet

### A. Create New Spreadsheet
1. Go to: https://sheets.google.com/
2. Click "Blank" to create new spreadsheet
3. Rename it to: "Real Estate Listings - Newton MA"

### B. Share with Service Account
1. Click the "Share" button (top-right)
2. In the JSON file you downloaded, find the "client_email" field
3. Copy that email address (looks like: `realestate-sheets@xxx.iam.gserviceaccount.com`)
4. Add this email to the share permissions
5. Set permission to "Editor"
6. Click "Send"

### C. Get Sheet ID
1. From your Google Sheet URL: 
   `https://docs.google.com/spreadsheets/d/1ABC123XYZ456/edit`
2. Copy the ID part: `1ABC123XYZ456`
3. This is your GOOGLE_SHEETS_ID

## ⚙️ Step 4: Update Configuration

Update your `.env` file with the actual Sheet ID:

```
GOOGLE_SHEETS_ID=YOUR_ACTUAL_SHEET_ID_HERE
GOOGLE_CREDENTIALS_PATH=./google_credentials.json
```

## 🚀 Step 5: Test Automated Upload

Run the upload script to test:
```
python upload_to_sheets.py
```

If successful, your CSV data will automatically appear in Google Sheets!

---

## 📋 Quick Checklist:
- [ ] Google Cloud project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled  
- [ ] Service account created with Editor role
- [ ] JSON key downloaded and renamed to `google_credentials.json`
- [ ] JSON file placed in project root folder
- [ ] Google Sheet created and shared with service account email
- [ ] Sheet ID copied and added to `.env` file
- [ ] Test upload script runs successfully

## ❗ Common Issues:
- **"Permission denied"**: Make sure you shared the sheet with the service account email
- **"File not found"**: Check that `google_credentials.json` is in the right location
- **"Invalid sheet ID"**: Verify you copied the correct ID from the Google Sheets URL