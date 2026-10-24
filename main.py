
from src.data_loader import build_aligned_data
from src.metrics import calculate_metrics, add_rolling_metrics, save_metrics
from src.stress_analysis import detect_stress_periods
from src.charts import (
    chart_cumulative_performance,
    chart_rolling_tracking_error,
    chart_daily_active_returns,
    FIGURES_DIR,
    PROCESSED_DIR,
)
import pandas as pd


def main():
    print("=" * 60)
    print("PASSIVE FUND TRACKING STRESS & BENCHMARK DRIFT ANALYSIS")
    print("=" * 60)

    # 1. Load, validate, and align NAV and TRI observations.
    data = build_aligned_data()

    # 2. Calculate tracking metrics and rolling tracking error.
    metrics = calculate_metrics(data)
    data = add_rolling_metrics(data)
    data.to_csv(PROCESSED_DIR / "aligned_daily_data.csv", index=False)
    save_metrics(metrics)

    # 3. Detect unusually elevated rolling tracking error.
    threshold, flagged_data, episodes = detect_stress_periods(data)

    # 4. Generate charts from the aligned dataset.
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    chart_cumulative_performance(data)
    chart_rolling_tracking_error(data)
    chart_daily_active_returns(data)

    print("\nSUMMARY")
    print("-" * 40)
    print(f"Analysis period: {metrics['start_date']} to {metrics['end_date']}")
    print(f"Valid daily returns: {metrics['valid_daily_returns']}")
    print(f"Annualized tracking error: "
          f"{metrics['annualized_tracking_error']:.6%}")
    print(f"Information ratio: {metrics['information_ratio']:.6f}")
    print(f"Stress threshold: {threshold:.6%}")
    print(f"Stress episodes: {len(episodes)}")
    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
