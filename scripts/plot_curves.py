"""
scripts/plot_curves.py
----------------------------------
Plots smoothed GAM curves for each era and exports PNGs to reports/figures.
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def main():
    curves = sorted(glob.glob(os.path.join(PROC_DIR, "curve_*.csv")))
    if not curves:
        print("[plot] no curves found. Run model_gam.py first.")
        return

    plt.figure()
    for fp in curves:
        df = pd.read_csv(fp)
        label = df["Era"].iloc[0]
        plt.plot(df["Age"], df["BPM_hat"], label=label)
    plt.xlabel("Age")
    plt.ylabel("Predicted BPM")
    plt.title("BPM Aging Curves by Era")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "bpm_aging_curves_by_era.png"), dpi=200)
    print("[plot] wrote figures/bpm_aging_curves_by_era.png")

if __name__ == "__main__":
    main()
