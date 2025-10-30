from app.utils.logger import logger
from app.scraper.zillow_scraper import scrape_zillow
from app.scraper.redfin_scraper import scrape_redfin
from app.scraper.realtor_scraper import scrape_realtor
from app.utils.mock_data import scrape_with_fallback
from app.integrations.database_manager import init_db, upsert_listing
from app.nlp.openai_classifier import classify_listing
from app.core.scoring_engine import score_listing
from app.integrations.google_sheets_uploader import upload_listings_to_sheet
import pandas as pd
import json
from datetime import datetime

def run_pipeline():
    logger.info("Pipeline started")
    init_db()
    all_listings = []
    # 1) Scrape sources with fallback to mock data
    from app.utils.config_loader import CONFIG
    use_mock = CONFIG["USE_MOCK_DATA"]
    
    z_results = scrape_with_fallback(lambda: scrape_zillow(max_pages=1), "Zillow", use_mock=use_mock)
    r_results = scrape_with_fallback(scrape_redfin, "Redfin", use_mock=use_mock)  
    rl_results = scrape_with_fallback(scrape_realtor, "Realtor", use_mock=use_mock)
    all_results = z_results + r_results + rl_results
    logger.info("Scraped total %d listings", len(all_results))

    # 2) Classify via LLM + simple NLP
    for l in all_results:
        raw_json = l.get("raw_json", {})
        if isinstance(raw_json, dict):
            raw_text = json.dumps(raw_json)
        else:
            raw_text = str(raw_json) if raw_json else ""
        text_for_class = l.get("address", "") + " " + raw_text
        fields = {
            "price": l.get("price"),
            "beds": l.get("beds"),
            "baths": l.get("baths"),
            "living_area": l.get("living_area")
        }
        label = classify_listing(text_for_class, fields)
        l["classified_label"] = label

        # 3) Enrichment (placeholder)
        # TODO: geocoding / lot size enrichment
        if "lot_size" not in l:
            l["lot_size"] = l.get("lot_size") or None

        # 4) Scoring
        l["score"] = score_listing(l)

        # 5) Save to DB
        l["raw_json"] = json.dumps(l.get("raw_json") or {})
        upsert_listing(l)

        all_listings.append(l)

    # 6) Export CSV and Google Sheets
    if all_listings:
        df = pd.DataFrame(all_listings)
        df.to_csv("./data/classified_listings.csv", index=False)
        upload_listings_to_sheet(df.to_dict(orient="records"), sheet_name="classified_listings")
    logger.info("Pipeline finished at %s", datetime.utcnow().isoformat())
