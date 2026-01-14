"""
scripts/fetch_bpm_bbr.py
----------------------------------
Scrapes player-season BPM and related columns from Basketball-Reference.
Saves per-season CSVs in data/raw/.

Note: Respect robots.txt and terms of use. This is for academic research.
"""

import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

os.makedirs(RAW_DIR, exist_ok=True)

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def fetch_season(season_end_year: int) -> pd.DataFrame:
    # Basketball-Reference "per 100" advanced page has BPM.
    url = f"https://www.basketball-reference.com/leagues/NBA_{season_end_year}_advanced.html"
    dfs = pd.read_html(url)
    # The main table is usually the first or contains 'Advanced'
    df = dfs[0]
    # Clean duplicate header rows
    df = df[df["Player"] != "Player"].copy()
    # Keep useful cols
    keep = ["Player", "Pos", "Age", "Tm", "G", "MP", "BPM"]
    df = df[keep]
    # Convert types
    for col in ["Age", "G", "MP", "BPM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Season"] = season_end_year - 1  # season start year
    return df

def main():
    load_dotenv()
    cfg = load_config()
    start = int(cfg["seasons"]["start"])
    end = int(cfg["seasons"]["end"])

    for y in range(start+1, end+1):  # season end years
        out_path = os.path.join(RAW_DIR, f"{y-1}_{y}_advanced.csv")
        if os.path.exists(out_path):
            print(f"[skip] {out_path}")
            continue
        try:
            df = fetch_season(y)
            df.to_csv(out_path, index=False)
            print(f"[ok] {out_path}  rows={len(df)}")
            time.sleep(1.0)  # be polite
        except Exception as e:
            print(f"[err] {y}: {e}")

if __name__ == "__main__":
    main()
