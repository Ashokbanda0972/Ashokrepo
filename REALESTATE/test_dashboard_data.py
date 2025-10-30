#!/usr/bin/env python3
"""
Quick test to verify dashboard data loading
"""

import pandas as pd
import sqlite3
import os

def test_dashboard_data():
    """Test both CSV and database data loading"""
    
    print("=== Dashboard Data Test ===")
    
    # Test CSV loading
    csv_path = "./data/classified_listings.csv"
    if os.path.exists(csv_path):
        try:
            df_csv = pd.read_csv(csv_path)
            print(f"✓ CSV: {len(df_csv)} listings loaded")
        except Exception as e:
            print(f"✗ CSV error: {e}")
    else:
        print("✗ CSV file not found")
    
    # Test database loading
    db_path = "./data/development_leads.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            query = """
            SELECT source, url, address, price, beds, baths, living_area, 
                   raw_json, classified_label, score, created_at as processed_at
            FROM listings 
            ORDER BY created_at DESC
            """
            df_db = pd.read_sql_query(query, conn)
            conn.close()
            print(f"✓ Database: {len(df_db)} listings loaded")
        except Exception as e:
            print(f"✗ Database error: {e}")
    else:
        print("✗ Database file not found")
    
    print("\n=== Test Complete ===")
    print("Dashboard should now work without database column errors!")

if __name__ == "__main__":
    test_dashboard_data()