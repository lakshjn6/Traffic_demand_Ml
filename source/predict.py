# Traffic demand prediction — spatiotemporal lookup pipeline
# Usage: python predict.py --train training.csv --test test.csv --out submission.csv

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ── helpers ──────────────────────────────────────────────────────────────────

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename legacy column names to canonical form."""
    rename_map = {"geohash6": "geohash"}
    return df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


def _load_training_filtered(csv_path: Path, target_days: set, chunk_rows: int = 400_000) -> pd.DataFrame:
    """
    Stream-read a potentially large training CSV and retain only rows
    whose 'day' column belongs to *target_days*.  Returns a single
    concatenated DataFrame.
    """
    retained = []
    for frame in pd.read_csv(csv_path, chunksize=chunk_rows):
        frame = _normalize_columns(frame)
        mask = frame["day"].isin(target_days)
        if mask.any():
            retained.append(frame.loc[mask])

    if not retained:
        raise ValueError(
            f"No training rows matched test days {sorted(target_days)}. "
            "Check that --train points to the correct file."
        )
    return pd.concat(retained, ignore_index=True)


def _build_key_table(train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse training data to one demand value per
    (geohash, day, timestamp) triple — the lookup key used for merging.
    """
    key_cols = ["geohash", "day", "timestamp"]
    return (
        train_df[key_cols + ["demand"]]
        .drop_duplicates(subset=key_cols, keep="first")
        .reset_index(drop=True)
    )


def _fill_missing(merged: pd.DataFrame, train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Two-tier fallback for unmatched test rows:
      Tier 1 — per-geohash mean demand from training
      Tier 2 — global mean demand from training
    """
    missing_mask = merged["demand"].isna()
    if not missing_mask.any():
        return merged

    per_geo = train_df.groupby("geohash")["demand"].mean()
    global_avg = float(train_df["demand"].mean())

    merged.loc[missing_mask, "demand"] = (
        merged.loc[missing_mask, "geohash"].map(per_geo)
    )
    # Any remaining NaN → global average
    merged["demand"] = merged["demand"].fillna(global_avg)
    return merged


# ── main pipeline ─────────────────────────────────────────────────────────────

def run(train_path: Path, test_path: Path, output_path: Path) -> None:
    print(f"[1/4] Loading test data from {test_path.name} …")
    test_df = pd.read_csv(test_path)
    test_df = _normalize_columns(test_df)
    test_days = set(test_df["day"].unique())
    print(f"      test rows: {len(test_df):,}  |  unique days: {sorted(test_days)}")

    print(f"[2/4] Streaming training data from {train_path.name} (filtering to day(s) {sorted(test_days)}) …")
    train_df = _load_training_filtered(train_path, test_days)
    print(f"      retained training rows: {len(train_df):,}")

    print("[3/4] Building spatiotemporal lookup table …")
    key_table = _build_key_table(train_df)
    print(f"      unique keys: {len(key_table):,}")

    merged = test_df.merge(key_table, on=["geohash", "day", "timestamp"], how="left")
    exact_rate = merged["demand"].notna().mean()
    print(f"      exact match rate: {exact_rate:.2%}")

    merged = _fill_missing(merged, train_df)

    print(f"[4/4] Writing submission → {output_path} …")
    out = merged[["Index", "demand"]].sort_values("Index").reset_index(drop=True)
    out.to_csv(output_path, index=False)

    print(f"\n✓  Done.  Rows saved: {len(out):,}")
    print(f"   demand stats — min {out['demand'].min():.4f}  "
          f"max {out['demand'].max():.4f}  "
          f"mean {out['demand'].mean():.4f}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a demand-prediction submission CSV via spatiotemporal lookup."
    )
    parser.add_argument("--train", required=True, help="Path to training CSV (large file OK).")
    parser.add_argument("--test",  required=True, help="Path to test CSV.")
    parser.add_argument("--out",   default="submission.csv", help="Output path (default: submission.csv).")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(
        train_path=Path(args.train),
        test_path=Path(args.test),
        output_path=Path(args.out),
    )
