#app/utils/config_loader.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key, default=None):
    return os.getenv(key, default)

CONFIG = {
    "SERPAPI_API_KEY": get_env("SERPAPI_API_KEY"),
    "OPENAI_API_KEY": get_env("OPENAI_API_KEY"),
    "GOOGLE_CREDENTIALS_PATH": get_env("GOOGLE_CREDENTIALS_PATH"),
    "GOOGLE_SHEETS_ID": get_env("GOOGLE_SHEETS_ID"),
    "DATABASE_PATH": get_env("DATABASE_PATH", "./data/development_leads.db"),
    "TARGET_CITY": get_env("TARGET_CITY", "Newton, MA"),
    "PLAYWRIGHT_HEADLESS": get_env("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
    "USE_MOCK_DATA": get_env("USE_MOCK_DATA", "true").lower() == "true"
}
