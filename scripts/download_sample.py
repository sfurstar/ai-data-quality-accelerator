#!/usr/bin/env python3
"""
scripts/download_sample.py
Downloads a sample of the NYC 311 Service Requests dataset (open government data)
and saves it to data/sample/structured/nyc_311_sample.csv

Dataset: NYC Open Data — 311 Service Requests from 2010 to Present
URL: https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9

Usage:
    python scripts/download_sample.py
    python scripts/download_sample.py --rows 5000
"""
import argparse
import sys
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "sample" / "structured" / "nyc_311_sample.csv"

# Socrata Open Data API endpoint — $limit controls row count, $order ensures consistency
BASE_URL = (
    "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
    "?$limit={limit}"
    "&$order=created_date+DESC"
    "&$select=unique_key,created_date,closed_date,agency,agency_name,"
    "complaint_type,descriptor,status,resolution_description,"
    "borough,incident_zip,latitude,longitude,incident_address"
)


def download(rows: int = 2000):
    try:
        import requests
    except ImportError:
        print("requests not installed. Run: pip install requests")
        sys.exit(1)

    url = BASE_URL.format(limit=rows)
    print(f"Downloading {rows:,} rows from NYC Open Data...")
    print(f"URL: {url[:80]}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(response.content)
    print(f"✅ Saved to {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")

    # Quick summary
    import pandas as pd
    df = pd.read_csv(OUTPUT_PATH)
    print(f"   Rows: {len(df):,}  |  Columns: {len(df.columns)}")
    null_pct = df.isnull().mean().mean()
    print(f"   Overall null rate: {null_pct:.1%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download NYC 311 sample dataset")
    parser.add_argument("--rows", type=int, default=2000, help="Number of rows to download (default: 2000)")
    args = parser.parse_args()
    download(args.rows)
