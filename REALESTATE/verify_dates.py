#!/usr/bin/env python3
"""
Verify CSV date updates
"""

import pandas as pd
from datetime import datetime
import os

def verify_csv_dates():
    """Check the dates in the CSV file"""
    
    csv_path = "./data/classified_listings.csv"
    
    if os.path.exists(csv_path):
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        print("=== CSV Date Verification ===")
        print(f"Total listings: {len(df)}")
        
        # Check processed_at dates
        df['processed_date'] = pd.to_datetime(df['processed_at']).dt.date
        
        print("\nProcessed dates:")
        date_counts = df['processed_date'].value_counts().sort_index()
        for date, count in date_counts.items():
            print(f"  {date}: {count} listings")
        
        # Check latest entry
        latest_entry = df.loc[df['processed_at'].idxmax()]
        print(f"\nLatest entry processed at: {latest_entry['processed_at']}")
        print(f"Latest entry address: {latest_entry['address']}")
        print(f"Latest entry price: ${latest_entry['price']:,}")
        
        # Check if data is fresh (today)
        today = datetime.now().date()
        fresh_data = df[df['processed_date'] == today]
        
        if len(fresh_data) > 0:
            print(f"\n✅ SUCCESS: Found {len(fresh_data)} fresh listings from today ({today})")
        else:
            print(f"\n⚠️  No fresh data from today ({today})")
        
        print(f"\nFile last modified: {datetime.fromtimestamp(os.path.getmtime(csv_path))}")
        
    else:
        print("❌ CSV file not found")

if __name__ == "__main__":
    verify_csv_dates()