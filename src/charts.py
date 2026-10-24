
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

DATA_FILE = PROCESSED_DIR / "aligned_daily_data.csv"
STRESS_FILE = PROCESSED_DIR / "stress_flags.csv"


def load_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"{DATA_FILE} not found. Run the data loader and metrics first."
        )

    data = pd.read_csv(DATA_FILE, parse_dates=["date"])
    data = data.sort_values("date").reset_index(drop=True)

    required = {
        "date", "nav", "tri", "fund_return",
        "benchmark_return", "active_return",
        "rolling_60d_tracking_error",
    }
    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {sorted(missing)}. "
            "Run `python -m src.metrics` first."
        )

    return data


def chart_cumulative_performance(data):
    """Compare cumulative growth of one unit invested in each series."""
    valid = data.dropna(
        subset=["fund_return", "benchmark_return"]
    ).copy()

    valid["fund_growth"] = (1 + valid["fund_return"]).cumprod()
    valid["benchmark_growth"] = (
        1 + valid["benchmark_return"]
    ).cumprod()

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        valid["date"],
        valid["fund_growth"],
        label="Kotak Nifty 50 Index Fund - Direct Growth",
    )
    ax.plot(
        valid["date"],
        valid["benchmark_growth"],
        label="Nifty 50 TRI",
    )

    ax.set_title("Cumulative Growth: Fund vs Nifty 50 TRI")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1 unit of initial investment")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output = FIGURES_DIR / "cumulative_performance.png"
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")


def chart_rolling_tracking_error(data):
    """Plot 60-observation annualized tracking error."""
    valid = data.dropna(
        subset=["rolling_60d_tracking_error"]
    ).copy()

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        valid["date"],
        valid["rolling_60d_tracking_error"] * 100,
        label="60-day rolling tracking error",
    )

    # Overlay the retrospective 95th-percentile threshold, if available.
    if STRESS_FILE.exists():
        stress = pd.read_csv(STRESS_FILE)
        if "stress_threshold" in stress.columns:
            thresholds = pd.to_numeric(
                stress["stress_threshold"], errors="coerce"
            ).dropna()

            if not thresholds.empty:
                ax.axhline(
                    thresholds.iloc[0] * 100,
                    linestyle="--",
                    label="95th-percentile sample threshold",
                )

    ax.set_title("Rolling Tracking Error")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized tracking error (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output = FIGURES_DIR / "rolling_tracking_error.png"
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")


def chart_daily_active_returns(data):
    """Plot daily fund return minus daily benchmark return."""
    valid = data.dropna(subset=["active_return"]).copy()

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        valid["date"],
        valid["active_return"] * 100,
        linewidth=0.8,
        label="Daily active return",
    )
    ax.axhline(0, linestyle="--")

    ax.set_title("Daily Active Returns: Fund Minus Nifty 50 TRI")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily active return (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output = FIGURES_DIR / "daily_active_returns.png"
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()

    chart_cumulative_performance(data)
    chart_rolling_tracking_error(data)
    chart_daily_active_returns(data)

    print("\nAll three charts created successfully.")


if __name__ == "__main__":
    main()
