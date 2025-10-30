import sqlite3
from sqlite3 import Connection
from typing import Dict, Any
import os
from app.utils.config_loader import CONFIG
from app.utils.logger import logger

DB_PATH = CONFIG["DATABASE_PATH"]
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    url TEXT UNIQUE,
    address TEXT,
    price INTEGER,
    beds INTEGER,
    baths REAL,
    living_area INTEGER,
    lot_size INTEGER,
    year_built INTEGER,
    dom INTEGER,
    status TEXT,
    raw_json TEXT,
    score REAL,
    classified_label TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn() -> Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)

def upsert_listing(listing: Dict[str, Any]):
    conn = get_conn()
    cur = conn.cursor()
    # Basic upsert pattern by URL uniqueness
    cur.execute("""
    INSERT INTO listings (source, url, address, price, beds, baths, living_area, lot_size, year_built, dom, status, raw_json, score, classified_label)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(url) DO UPDATE SET
        price=excluded.price,
        beds=excluded.beds,
        baths=excluded.baths,
        living_area=excluded.living_area,
        lot_size=excluded.lot_size,
        year_built=excluded.year_built,
        dom=excluded.dom,
        status=excluded.status,
        raw_json=excluded.raw_json,
        score=excluded.score,
        classified_label=excluded.classified_label;
    """, (
        listing.get("source"),
        listing.get("url"),
        listing.get("address"),
        listing.get("price"),
        listing.get("beds"),
        listing.get("baths"),
        listing.get("living_area"),
        listing.get("lot_size"),
        listing.get("year_built"),
        listing.get("dom"),
        listing.get("status"),
        listing.get("raw_json"),
        listing.get("score"),
        listing.get("classified_label")
    ))
    conn.commit()
    conn.close()
    logger.info("Upserted listing: %s", listing.get("url"))
