# NBA Player Prime Replication (BPM) — 1990–2025

**Goal:** Replicate classic "basketball prime" results with **Box Plus/Minus (BPM)** and test whether peak age shifted in the modern era (2015–2025).

## Quickstart
```bash
# 1) Create venv (Unix/macOS)
python -m venv venv && source venv/bin/activate

#    or on Windows (PowerShell)
python -m venv venv ; .\venv\Scripts\Activate.ps1

# 2) Install deps
pip install -r requirements.txt

# 3) (Optional) set up .env
cp .env.example .env

# 4) Fetch data (edit config/config.yaml if needed)
python scripts/fetch_bpm_bbr.py

# 5) Clean & merge
python scripts/clean_merge.py

# 6) Model & plot (GAM)
python scripts/model_gam.py
python scripts/plot_curves.py
```

## Project layout
```
data/
  raw/         # per-season scraped CSVs
  clean/       # cleaned tables
  processed/   # modeling-ready
scripts/       # python scripts (ETL, modeling, viz)
notebooks/     # exploratory analysis
config/        # config.yaml (seasons, thresholds)
reports/       # figures, tables, writeups
```
