
import numpy as np
import pandas as pd
import pytest

from src.metrics import calculate_metrics, add_rolling_metrics


def make_sample_data():
    """Create a small dataset with known fund and benchmark returns."""
    dates = pd.date_range("2026-01-01", periods=5, freq="D")

    # Both series grow by 1% per observation.
    fund_returns = [np.nan, 0.01, 0.01, 0.01, 0.01]
    benchmark_returns = [np.nan, 0.01, 0.01, 0.01, 0.01]

    nav = [100.0]
    tri = [1000.0]

    for _ in range(4):
        nav.append(nav[-1] * 1.01)
        tri.append(tri[-1] * 1.01)

    return pd.DataFrame({
        "date": dates,
        "nav": nav,
        "tri": tri,
        "fund_return": fund_returns,
        "benchmark_return": benchmark_returns,
        "active_return": [
            np.nan, 0.0, 0.0, 0.0, 0.0
        ],
    })


def test_equal_returns_have_zero_tracking_error():
    data = make_sample_data()

    metrics = calculate_metrics(data)

    assert metrics["fund_cumulative_return"] == pytest.approx(
        metrics["benchmark_cumulative_return"]
    )
    assert metrics["cumulative_return_gap"] == pytest.approx(0.0)
    assert metrics["annualized_tracking_error"] == pytest.approx(0.0)
    assert np.isnan(metrics["information_ratio"])


def test_tracking_error_is_nonnegative():
    data = make_sample_data()
    data["active_return"] = [np.nan, 0.001, -0.001, 0.002, -0.002]

    metrics = calculate_metrics(data)

    assert metrics["annualized_tracking_error"] >= 0


def test_missing_required_column_raises_error():
    data = make_sample_data().drop(columns=["tri"])

    with pytest.raises(ValueError, match="Missing required columns"):
        calculate_metrics(data)


def test_rolling_tracking_error_needs_full_window():
    data = pd.DataFrame({
        "active_return": [0.001] * 60
    })

    result = add_rolling_metrics(data)

    assert result["rolling_60d_tracking_error"].iloc[:59].isna().all()
    assert result["rolling_60d_tracking_error"].iloc[59] == pytest.approx(0.0)
