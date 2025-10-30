import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from app.utils.config_loader import CONFIG
from app.utils.logger import logger

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet_client():
    creds_path = CONFIG["GOOGLE_CREDENTIALS_PATH"]
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def upload_listings_to_sheet(listings: list, sheet_id=None, sheet_name="Sheet1"):
    if sheet_id is None:
        sheet_id = CONFIG["GOOGLE_SHEETS_ID"]
    client = get_sheet_client()
    sheet = client.open_by_key(sheet_id)
    try:
        worksheet = sheet.worksheet(sheet_name)
    except Exception:
        worksheet = sheet.add_worksheet(title=sheet_name, rows="1000", cols="30")
    df = pd.DataFrame(listings)
    # Ensure columns order
    df = df[sorted(df.columns)]
    # Clear and update
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
    logger.info("Uploaded %d rows to sheet %s/%s", len(df), sheet_id, sheet_name)
