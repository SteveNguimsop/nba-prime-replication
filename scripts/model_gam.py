"""
scripts/model_gam.py
----------------------------------
Fits simple GAM aging curves per era using pygam.
Writes out the estimated peak ages and prediction grids.
"""

import os
import numpy as np
import pandas as pd
from pygam import LinearGAM, s

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
OUT_FIG = os.path.join(BASE_DIR, "reports", "figures")

os.makedirs(OUT_FIG, exist_ok=True)

def fit_gam(df):
    # X is age only for basic curve
    X = df[["Age"]].values
    y = df["BPM"].values
    gam = LinearGAM(s(0)).fit(X, y)
    grid = np.linspace(df["Age"].min(), df["Age"].max(), 200)
    preds = gam.predict(grid)
    peak_age = float(grid[np.argmax(preds)])
    return gam, grid, preds, peak_age

def main():
    df = pd.read_csv(os.path.join(PROC_DIR, "for_model.csv"))
    results = []

    for era in df["Era"].dropna().unique():
        sub = df[df["Era"] == era].copy()
        if len(sub) < 200:
            continue
        _, grid, preds, peak = fit_gam(sub)
        out = pd.DataFrame({"Era": era, "Age": grid, "BPM_hat": preds})
        out.to_csv(os.path.join(PROC_DIR, f"curve_{era.replace(' ', '_')}.csv"), index=False)
        results.append({"Era": era, "PeakAge": peak})

    if results:
        pd.DataFrame(results).to_csv(os.path.join(PROC_DIR, "peak_ages.csv"), index=False)
        print("[model] wrote peak_ages.csv")

if __name__ == "__main__":
    main()
