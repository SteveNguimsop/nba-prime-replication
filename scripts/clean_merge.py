"""
scripts/clean_merge.py
----------------------------------
Loads per-season CSVs from data/raw, applies filters, and writes:
- data/clean/player_seasons.csv  (row = player-season)
- data/processed/for_model.csv   (minimal columns for modeling)

This version supports:
- BBR CSV exports that have "Team" instead of "Tm"
- Manually-downloaded CSVs that do NOT include a Season column
  (we infer Season from the filename: YYYY_YYYY_advanced.csv)
"""

import os
import glob
import re
import pandas as pd
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def era_label(season_start: int, eras: list[dict]) -> str:
    for e in eras:
        if int(e["start"]) <= season_start <= int(e["end"]):
            return e["name"]
    return "Unknown"


def infer_season_start_from_filename(fp: str) -> int:
    """
    Expects filenames like:
      1990_1991_advanced.csv
      2015_2016_advanced.csv

    Returns season start year (e.g., 1990, 2015).
    """
    name = os.path.basename(fp)
    m = re.search(r"(\d{4})_(\d{4})_advanced\.csv$", name)
    if not m:
        raise ValueError(
            f"Could not infer season from filename: {name}\n"
            f"Expected format like 1990_1991_advanced.csv"
        )
    return int(m.group(1))


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes column names across different exports.
    We want to end up with these canonical columns present:
      Player, Age, Team, Position, Minutes, BPM
    """
    # Strip whitespace from column headers
    df.columns = [c.strip() for c in df.columns]

    # Some exports use Team instead of Tm
    if "Tm" not in df.columns and "Team" in df.columns:
        df = df.rename(columns={"Team": "Tm"})

    # Some exports could have slightly different labels; keep it simple.
    rename_map = {
        "Pos": "Position",
        "Tm": "Team",
        "MP": "Minutes",
        "BPM": "BPM",
        "Age": "Age",
        "Player": "Player",
    }
    df = df.rename(columns=rename_map)

    return df


def main():
    cfg = load_config()
    min_minutes = int(cfg.get("min_minutes", 0))
    eras = cfg.get("eras", [])

    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not files:
        print(f"[clean] No CSV files found in {RAW_DIR}")
        return

    frames = []

    for fp in files:
        season_start = infer_season_start_from_filename(fp)
        df = pd.read_csv(fp)

        df = standardize_columns(df)

        # Ensure required columns exist
        required = ["Player", "Age", "Team", "Position", "Minutes", "BPM"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"[skip] {os.path.basename(fp)} missing columns: {missing}")
            continue

        # Convert key columns to numeric where needed
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
        df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")
        df["BPM"] = pd.to_numeric(df["BPM"], errors="coerce")

        # Add Season + Era
        df["Season"] = season_start
        df["Era"] = era_label(season_start, eras)

        # Filter by minutes (after numeric conversion)
        df = df[df["Minutes"] >= min_minutes].copy()

        # Keep only useful columns for the pipeline
        keep_cols = ["Player", "Age", "Team", "Position", "Minutes", "BPM", "Season", "Era"]
        df = df[keep_cols]

        frames.append(df)

    all_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    all_path = os.path.join(CLEAN_DIR, "player_seasons.csv")
    all_df.to_csv(all_path, index=False)

    # Minimal modeling table
    model_cols = ["Player", "Age", "BPM", "Minutes", "Season", "Position", "Era"]
    model_df = all_df[model_cols].dropna() if not all_df.empty else pd.DataFrame(columns=model_cols)
    model_path = os.path.join(PROC_DIR, "for_model.csv")
    model_df.to_csv(model_path, index=False)

    print(f"[clean] files={len(files)}  rows={len(all_df)}  model_rows={len(model_df)}")
    print(f"[out]  {all_path}")
    print(f"[out]  {model_path}")


if __name__ == "__main__":
    main()
