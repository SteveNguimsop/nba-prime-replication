# -*- coding: utf-8 -*-

"""
model_gam.py

Fits GAM aging curves for NBA players using BPM.
To reduce survivorship bias:
- Restricts ages to a default window (20-35)
- Collapses player-seasons into age-level weighted averages (weights=Minutes)

Input:
- data/processed/for_model.csv

Outputs:
- data/processed/peak_ages.csv
- data/processed/curve_<era>.csv
"""

import os
import numpy as np
import pandas as pd
from pygam import LinearGAM, s


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")


def prep_age_table(df, min_age=20, max_age=35, min_players=50):
    """
    Collapse to age-level weighted means to reduce survivorship bias.
    Returns a table with columns: Age, BPM_mean, Minutes_sum, N (players/rows)
    """
    # Ensure numeric
    df = df.copy()
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["BPM"] = pd.to_numeric(df["BPM"], errors="coerce")
    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")

    # Basic cleaning
    df = df.dropna(subset=["Age", "BPM", "Minutes"])
    df = df[(df["Age"] >= min_age) & (df["Age"] <= max_age)]
    df = df[df["Minutes"] > 0]

    # Weighted mean BPM by age (weights = Minutes)
    g = df.groupby("Age", as_index=False).apply(
        lambda x: pd.Series({
            "BPM_mean": np.average(x["BPM"], weights=x["Minutes"]),
            "Minutes_sum": x["Minutes"].sum(),
            "N": len(x)
        })
    ).reset_index(drop=True)

    # Require enough sample size per age so the curve isn't noisy
    g = g[g["N"] >= min_players].sort_values("Age").reset_index(drop=True)
    return g


def fit_gam_on_age_table(age_table):
    """
    Fit GAM: BPM_mean ~ s(Age) with sample weights = Minutes_sum
    Returns grid, preds, peak_age
    """
    X = age_table[["Age"]].values
    y = age_table["BPM_mean"].values
    w = age_table["Minutes_sum"].values

    # Gridsearch chooses smoothing (lam) automatically
    gam = LinearGAM(s(0, n_splines=10)).gridsearch(X, y, weights=w)

    grid = np.linspace(age_table["Age"].min(), age_table["Age"].max(), 200)
    preds = gam.predict(grid)

    peak_age = float(grid[np.argmax(preds)])
    return grid, preds, peak_age


def main():
    in_path = os.path.join(PROC_DIR, "for_model.csv")
    df = pd.read_csv(in_path)

    # You can change this window if you want, but 20-35 is standard for "prime age"
    MIN_AGE = 20
    MAX_AGE = 35

    results = []

    for era in df["Era"].dropna().unique():
        sub = df[df["Era"] == era].copy()

        age_table = prep_age_table(
            sub,
            min_age=MIN_AGE,
            max_age=MAX_AGE,
            min_players=50
        )

        if len(age_table) < 6:
            print(f"[model] Skipping {era}: not enough age points after filtering.")
            continue

        grid, preds, peak = fit_gam_on_age_table(age_table)

        print(f"[model] {era}: peak_age={peak:.2f} (age_window={MIN_AGE}-{MAX_AGE})")

        curve_out = pd.DataFrame({
            "Era": era,
            "Age": grid,
            "BPM_hat": preds
        })

        curve_out.to_csv(
            os.path.join(PROC_DIR, f"curve_{era.replace(' ', '_')}.csv"),
            index=False
        )

        results.append({"Era": era, "PeakAge": peak})

    if results:
        out_path = os.path.join(PROC_DIR, "peak_ages.csv")
        pd.DataFrame(results).to_csv(out_path, index=False)
        print("[model] wrote peak_ages.csv")


if __name__ == "__main__":
    main()
