
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = PROCESSED_DIR / "aligned_daily_data.csv"
OUTPUT_FLAGS = PROCESSED_DIR / "stress_flags.csv"
OUTPUT_EPISODES = PROCESSED_DIR / "stress_episodes.csv"

ROLLING_COLUMN = "rolling_60d_tracking_error"
THRESHOLD_QUANTILE = 0.95


def detect_stress_periods(data: pd.DataFrame):
    """Flag elevated rolling tracking error and summarize episodes."""
    required = {"date", ROLLING_COLUMN}
    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            "Run `python -m src.metrics` first."
        )

    result = data.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result[ROLLING_COLUMN] = pd.to_numeric(
        result[ROLLING_COLUMN], errors="coerce"
    )

    valid = result[ROLLING_COLUMN].dropna()

    if len(valid) < 20:
        raise ValueError(
            "Too few valid rolling tracking-error observations "
            "to define a meaningful sample threshold."
        )

    threshold = valid.quantile(THRESHOLD_QUANTILE)

    result["stress_threshold"] = threshold
    result["elevated_tracking_error"] = (
        result[ROLLING_COLUMN] > threshold
    )

    # Exclude rows without a rolling estimate from stress flags.
    result.loc[result[ROLLING_COLUMN].isna(),
               "elevated_tracking_error"] = False

    # Assign an episode number whenever the flag changes.
    result["episode_group"] = (
        result["elevated_tracking_error"]
        .ne(result["elevated_tracking_error"].shift())
        .cumsum()
    )

    elevated = result[result["elevated_tracking_error"]].copy()

    if elevated.empty:
        episodes = pd.DataFrame(
            columns=[
                "episode_id", "start_date", "end_date",
                "observations", "max_rolling_tracking_error",
                "mean_rolling_tracking_error",
            ]
        )
    else:
        episodes = (
            elevated.groupby("episode_group")
            .agg(
                start_date=("date", "min"),
                end_date=("date", "max"),
                observations=("date", "size"),
                max_rolling_tracking_error=(ROLLING_COLUMN, "max"),
                mean_rolling_tracking_error=(ROLLING_COLUMN, "mean"),
            )
            .reset_index(drop=True)
        )
        episodes.insert(
            0, "episode_id",
            range(1, len(episodes) + 1)
        )

    result.drop(columns=["episode_group"]).to_csv(
        OUTPUT_FLAGS, index=False
    )
    episodes.to_csv(OUTPUT_EPISODES, index=False)

    return threshold, result, episodes


if __name__ == "__main__":
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} not found. Run `python -m src.metrics` first."
        )

    data = pd.read_csv(INPUT_FILE, parse_dates=["date"])

    threshold, flagged_data, episodes = detect_stress_periods(data)

    print("\nTRACKING-ERROR STRESS ANALYSIS")
    print("=" * 40)
    print(f"Threshold quantile: {THRESHOLD_QUANTILE:.0%}")
    print(f"Threshold: {threshold:.6%}")
    print(
        "Elevated observations:",
        int(flagged_data["elevated_tracking_error"].sum()),
    )
    print(f"Stress episodes: {len(episodes)}")
    print(f"Saved flags to: {OUTPUT_FLAGS}")
    print(f"Saved episodes to: {OUTPUT_EPISODES}")

    if not episodes.empty:
        print("\nStress episodes:")
        print(episodes.to_string(index=False))
