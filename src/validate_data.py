
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_loader import read_nav_files, read_benchmark_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

ALIGNED_FILE = PROCESSED_DIR / "aligned_daily_data.csv"
REPORT_FILE = PROCESSED_DIR / "data_validation_report.txt"


def validate_series(name, df, date_col, value_col):
    """Report basic date, duplicate, missing-value and level checks."""
    print(f"\n{name}")
    print("-" * 50)

    print(f"Rows: {len(df)}")
    print(f"Missing dates: {df[date_col].isna().sum()}")
    print(f"Missing values: {df[value_col].isna().sum()}")
    print(f"Duplicate dates: {df[date_col].duplicated().sum()}")

    valid = df.dropna(subset=[date_col, value_col]).sort_values(date_col)

    if not valid.empty:
        print(f"First date: {valid[date_col].min().date()}")
        print(f"Last date: {valid[date_col].max().date()}")
        print(f"First level: {valid[value_col].iloc[0]:.6f}")
        print(f"Last level: {valid[value_col].iloc[-1]:.6f}")

        if (valid[value_col] <= 0).any():
            print("WARNING: Non-positive levels found.")
        else:
            print("All levels are positive.")


def main():
    lines = []
    original_print = print

    # Capture printed output so a permanent report can be saved.
    import io
    import contextlib

    buffer = io.StringIO()

    with contextlib.redirect_stdout(buffer):
        nav = read_nav_files()
        tri = read_benchmark_file()

        validate_series("FILTERED FUND NAV", nav, "date", "nav")
        validate_series("BENCHMARK TRI", tri, "date", "tri")

        print("\nALIGNED DATA CHECKS")
        print("-" * 50)

        if not ALIGNED_FILE.exists():
            raise FileNotFoundError(
                f"{ALIGNED_FILE} not found. Run `python main.py` first."
            )

        aligned = pd.read_csv(ALIGNED_FILE, parse_dates=["date"])
        print(f"Aligned rows: {len(aligned)}")
        print(f"Duplicate aligned dates: {aligned['date'].duplicated().sum()}")

        # Verify that aligned levels match the source files on common dates.
        check = aligned.merge(
            nav.rename(columns={"nav": "source_nav"}),
            on="date",
            how="left",
        ).merge(
            tri.rename(columns={"tri": "source_tri"}),
            on="date",
            how="left",
        )

        nav_mismatch = (
            check["nav"].sub(check["source_nav"]).abs() > 1e-8
        ).sum()
        tri_mismatch = (
            check["tri"].sub(check["source_tri"]).abs() > 1e-6
        ).sum()

        print(f"NAV level mismatches: {nav_mismatch}")
        print(f"TRI level mismatches: {tri_mismatch}")

        # Recompute returns from the aligned levels.
        expected_fund = check["nav"].pct_change()
        expected_tri = check["tri"].pct_change()

        fund_return_mismatch = (
            check["fund_return"].sub(expected_fund).abs() > 1e-8
        ).sum()
        tri_return_mismatch = (
            check["benchmark_return"].sub(expected_tri).abs() > 1e-8
        ).sum()

        print(f"Fund return mismatches: {fund_return_mismatch}")
        print(f"Benchmark return mismatches: {tri_return_mismatch}")

        valid = check.dropna(
            subset=["fund_return", "benchmark_return"]
        ).copy()

        fund_cumulative = (1 + valid["fund_return"]).prod() - 1
        tri_cumulative = (1 + valid["benchmark_return"]).prod() - 1

        fund_level_return = (
            check["nav"].iloc[-1] / check["nav"].iloc[0] - 1
        )
        tri_level_return = (
            check["tri"].iloc[-1] / check["tri"].iloc[0] - 1
        )

        print("\nCUMULATIVE RETURN RECONCILIATION")
        print("-" * 50)
        print(f"Fund compounded daily returns: {fund_cumulative:.8%}")
        print(f"Fund first-to-last NAV return: {fund_level_return:.8%}")
        print(f"TRI compounded daily returns: {tri_cumulative:.8%}")
        print(f"TRI first-to-last level return: {tri_level_return:.8%}")

        print("\nDAILY RETURN EXTREMES")
        print("-" * 50)
        print(
            "Minimum fund daily return:",
            f"{valid['fund_return'].min():.4%}",
        )
        print(
            "Maximum fund daily return:",
            f"{valid['fund_return'].max():.4%}",
        )
        print(
            "Minimum TRI daily return:",
            f"{valid['benchmark_return'].min():.4%}",
        )
        print(
            "Maximum TRI daily return:",
            f"{valid['benchmark_return'].max():.4%}",
        )

        print("\nREVIEW FLAGS")
        print("-" * 50)

        if nav_mismatch or tri_mismatch:
            print("FAIL: Aligned levels do not match source data.")
        else:
            print("PASS: Aligned levels match source data.")

        if fund_return_mismatch or tri_return_mismatch:
            print("FAIL: Stored returns differ from recomputed returns.")
        else:
            print("PASS: Stored returns match recomputed returns.")

        if not np.isclose(fund_cumulative, fund_level_return, atol=1e-8):
            print("FAIL: Fund cumulative return does not reconcile.")
        else:
            print("PASS: Fund cumulative return reconciles.")

        if not np.isclose(tri_cumulative, tri_level_return, atol=1e-8):
            print("FAIL: TRI cumulative return does not reconcile.")
        else:
            print("PASS: TRI cumulative return reconciles.")

    report = buffer.getvalue()
    original_print(report)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    original_print(f"\nValidation report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()