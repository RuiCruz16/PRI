import argparse
import re
import sys
from pathlib import Path
import pandas as pd


# Primary columns we care about (only these count toward "missing" for the audit)
PRIMARY_COLS = [
    "overview",
    "symptoms",
    "causes",
    "diagnosis and tests",
    "management and treatment",
    "outlook / prognosis",
    "prevention",
    "living with",
]


def is_missing(val) -> bool:
    """
    Determine whether a cell should be treated as missing for our purposes:
    - NaN / empty
    - "" (after stripping)
    - "Not available" (case-insensitive; with or without parentheses)
    """
    if pd.isna(val):
        return True
    s = str(val).strip().lower()
    if s == "":
        return True
    # normalize variants like "(Not available)"
    s = re.sub(r"[()]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s == "not available"


def main():
    parser = argparse.ArgumentParser(
        description="Audit missing values across the primary columns"
    )
    parser.add_argument(
        "--csv",
        default="diseases_dataset.csv",
        help="Path to the input CSV (default: diseases_dataset.csv)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=2,
        help="Select diseases with more than N missing among primary columns (default: 2)",
    )
    parser.add_argument(
        "--starts-with",
        default=None,
        help="Optional: filter by the first letter of the disease name (e.g., C).",
    )
    parser.add_argument(
        "--out",
        default="missing_values.csv",
        help="Path to the output CSV (default: missing_values.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # Map canonical primary columns (lowercase) to actual CSV column names (case-insensitive)
    cols_map = {}  # canonical -> actual
    lower_cols = {c.lower(): c for c in df.columns}
    missing_any = False
    for c in PRIMARY_COLS:
        if c in lower_cols:
            cols_map[c] = lower_cols[c]
        else:
            print(f"Warning: primary column not found in CSV: {c}", file=sys.stderr)
            missing_any = True
    if missing_any:
        print("Proceeding with the primary columns that exist.", file=sys.stderr)

    # Only use primary columns that are present in the file
    present_primary = [cols_map[c] for c in PRIMARY_COLS if c in cols_map]

    # Optional filter by the first letter of the disease name
    if args.starts_with:
        sw = args.starts_with.strip().lower()
        name_col = lower_cols.get("disease name") or lower_cols.get("name")
        if name_col:
            df = df[df[name_col].astype(str).str.strip().str.lower().str.startswith(sw)]

    # Build a boolean mask of missingness across primary columns only
    miss_mask = df[present_primary].applymap(is_missing)

    # Per-column missing counts and percentages
    per_col_counts = miss_mask.sum().rename_axis("column").reset_index(name="missing_count")
    per_col_pct = (miss_mask.mean() * 100).round(2).rename_axis("column").reset_index(name="missing_pct")

    # Per-row missing count across primary columns
    df["_primary_missing_count"] = miss_mask.sum(axis=1)

    # Which primary columns are missing for each row (comma-separated)
    df["_which_primary_missing"] = miss_mask.apply(
        lambda row: ", ".join(col for col, miss in row.items() if miss),
        axis=1,
    )

    # Filter: rows with more than N missing among the primary columns
    filtered = df[df["_primary_missing_count"] > args.threshold].copy()

    # Prepare a concise view for export
    id_col = lower_cols.get("id")
    name_col = lower_cols.get("disease name") or lower_cols.get("name")
    view_cols = [c for c in [id_col, name_col, "_primary_missing_count", "_which_primary_missing"] if c]
    if name_col and name_col in view_cols:
        sort_cols = ["_primary_missing_count", name_col]
    else:
        sort_cols = ["_primary_missing_count"]
    filtered_view = filtered[view_cols].sort_values(by=sort_cols, ascending=[False, True])

    # Print summary to the console
    total_rows = len(df)
    num_filtered = len(filtered_view)
    print("=" * 60)
    print(f"Total diseases (after starts-with={args.starts_with!r} filter): {total_rows}")
    print(f"Diseases with > {args.threshold} missing among primary columns: {num_filtered}")
    print("-" * 60)
    print("Missing by column (counts):")
    print(per_col_counts.to_string(index=False))
    print("-" * 60)
    print("Missing by column (percent):")
    print(per_col_pct.to_string(index=False))
    print("-" * 60)

    # Save the result
    out_path = Path(args.out)
    filtered_view.to_csv(out_path, index=False)
    print(f"Report saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
