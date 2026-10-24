
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TRADING_DAYS = 252
ROLLING_WINDOW = 60


def calculate_metrics(data: pd.DataFrame) -> dict:
    """Calculate benchmark-relative performance and tracking metrics."""
    required = {"date", "nav", "tri", "fund_return",
                "benchmark_return", "active_return"}
    missing = required - set(data.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    valid = data.dropna(
        subset=["fund_return", "benchmark_return", "active_return"]
    ).copy()

    if len(valid) < 2:
        raise ValueError("Not enough valid daily returns to calculate metrics.")

    active = valid["active_return"].astype(float)
    fund_returns = valid["fund_return"].astype(float)
    benchmark_returns = valid["benchmark_return"].astype(float)

    # Annualized tracking error: sample standard deviation of daily
    # active returns multiplied by sqrt(252).
    daily_active_std = active.std(ddof=1)
    tracking_error = daily_active_std * np.sqrt(TRADING_DAYS)

    # Annualized arithmetic mean active return.
    annualized_mean_active_return = active.mean() * TRADING_DAYS

    information_ratio = (
        annualized_mean_active_return / tracking_error
        if tracking_error > 0 else np.nan
    )

    # Cumulative returns over the observed aligned return period.
    fund_cumulative_return = (1 + fund_returns).prod() - 1
    benchmark_cumulative_return = (1 + benchmark_returns).prod() - 1

    # Difference between cumulative fund and benchmark returns.
    cumulative_return_gap = (
        fund_cumulative_return - benchmark_cumulative_return
    )

    # Difference in ending index/fund levels, expressed as a percentage
    # of the benchmark's cumulative growth factor.
    relative_wealth_gap = (
        (1 + fund_cumulative_return)
        / (1 + benchmark_cumulative_return) - 1
    )

    metrics = {
        "start_date": valid["date"].min().strftime("%Y-%m-%d"),
        "end_date": valid["date"].max().strftime("%Y-%m-%d"),
        "valid_daily_returns": int(len(valid)),
        "fund_cumulative_return": float(fund_cumulative_return),
        "benchmark_cumulative_return": float(benchmark_cumulative_return),
        "cumulative_return_gap": float(cumulative_return_gap),
        "relative_wealth_gap": float(relative_wealth_gap),
        "mean_daily_active_return": float(active.mean()),
        "annualized_mean_active_return": float(
            annualized_mean_active_return
        ),
        "annualized_tracking_error": float(tracking_error),
        "information_ratio": float(information_ratio),
        "maximum_absolute_daily_active_return": float(active.abs().max()),
    }

    return metrics


def add_rolling_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Add a 60-observation rolling annualized tracking error."""
    result = data.copy()

    result["rolling_60d_tracking_error"] = (
        result["active_return"]
        .rolling(window=ROLLING_WINDOW, min_periods=ROLLING_WINDOW)
        .std(ddof=1)
        * np.sqrt(TRADING_DAYS)
    )

    return result


def save_metrics(metrics: dict) -> Path:
    """Save summary metrics as a two-column CSV."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "summary_metrics.csv"

    pd.DataFrame(
        [{"metric": key, "value": value}
         for key, value in metrics.items()]
    ).to_csv(output_path, index=False)

    return output_path


if __name__ == "__main__":
    aligned_path = PROCESSED_DIR / "aligned_daily_data.csv"

    if not aligned_path.exists():
        raise FileNotFoundError(
            f"{aligned_path} not found. Run `python -m src.data_loader` first."
        )

    data = pd.read_csv(aligned_path, parse_dates=["date"])

    metrics = calculate_metrics(data)
    rolling_data = add_rolling_metrics(data)

    rolling_path = PROCESSED_DIR / "aligned_daily_data.csv"
    rolling_data.to_csv(rolling_path, index=False)

    metrics_path = save_metrics(metrics)

    print("\nBENCHMARK TRACKING METRICS")
    print("=" * 40)

    for key, value in metrics.items():
        if isinstance(value, float):
            if "return" in key or "error" in key:
                print(f"{key}: {value:.6%}")
            else:
                print(f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")

    print(f"\nSummary saved to: {metrics_path}")
    print(f"Rolling tracking error saved in: {rolling_path}")
