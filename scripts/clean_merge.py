"""
scripts/clean_merge.py
----------------------------------
Loads per-season CSVs from data/raw, applies filters, and writes:
- data/clean/player_seasons.csv  (row = player-season)
- data/processed/for_model.csv   (minimal columns for modeling)
"""

import os
import glob
import pandas as pd
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def era_label(season_start, eras):
    for e in eras:
        if e["start"] <= season_start <= e["end"]:
            return e["name"]
    return "Unknown"

def main():
    cfg = load_config()
    min_minutes = int(cfg["min_minutes"])
    eras = cfg["eras"]

    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    frames = []
    for fp in files:
        df = pd.read_csv(fp)
        # Filter by minutes
        df = df[df["MP"] >= min_minutes].copy()
        # Standardize columns
        df.rename(columns={"Pos": "Position", "Tm": "Team", "Age": "Age", "BPM": "BPM", "MP": "Minutes"}, inplace=True)
        # Era label
        df["Era"] = df["Season"].apply(lambda s: era_label(int(s), eras))
        frames.append(df)

    all_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    all_df.to_csv(os.path.join(CLEAN_DIR, "player_seasons.csv"), index=False)

    # Minimal modeling table
    model_cols = ["Player", "Age", "BPM", "Minutes", "Season", "Position", "Era"]
    model_df = all_df[model_cols].dropna()
    model_df.to_csv(os.path.join(PROC_DIR, "for_model.csv"), index=False)

    print(f"[clean] rows={len(all_df)}  model_rows={len(model_df)}")

if __name__ == "__main__":
    main()
