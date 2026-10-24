
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
NAV_DIR = PROJECT_ROOT / "data" / "raw" / "nav"
BENCHMARK_DIR = PROJECT_ROOT / "data" / "raw" / "benchmark"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Kotak Nifty 50 Index Fund - Direct Plan - Growth
TARGET_SCHEME_CODE = "148978"
TARGET_ISIN = "INF174KA1HA7"

NAV_FILES = sorted(NAV_DIR.glob("*.txt"))
BENCHMARK_FILES = sorted(BENCHMARK_DIR.glob("*.csv"))


def read_nav_files() -> pd.DataFrame:
    """Read AMFI NAV files and retain the target Kotak fund."""
    if not NAV_FILES:
        raise FileNotFoundError(
            f"No NAV .txt files found in {NAV_DIR}"
        )

    frames = []

    for file_path in NAV_FILES:
        df = pd.read_csv(
            file_path,
            sep=";",
            dtype=str,
            encoding="utf-8-sig",
            on_bad_lines="warn",
        )

        df.columns = df.columns.str.strip()

        required = {
            "Scheme Code",
            "NAV Name",
            "Net Asset Value",
            "Date",
        }
        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"{file_path.name} is missing columns: {sorted(missing)}"
            )

        # Match by scheme code or ISIN, where available.
        scheme_code = df["Scheme Code"].fillna("").str.strip()
        isin_match = pd.Series(False, index=df.index)

        for column in ("ISIN Div Payout/ISIN Growth",
                       "ISIN Div Reinvestment"):
            if column in df.columns:
                isin_match |= (
                    df[column].fillna("").str.strip() == TARGET_ISIN
                )

        target = df[
            (scheme_code == TARGET_SCHEME_CODE) | isin_match
        ].copy()

        if not target.empty:
            target["source_file"] = file_path.name
            frames.append(target)

    if not frames:
        raise ValueError(
            "Target fund not found. Check scheme code and ISIN."
        )

    nav = pd.concat(frames, ignore_index=True)

    nav["date"] = pd.to_datetime(
        nav["Date"].str.strip(),
        format="%d-%b-%Y",
        errors="coerce",
    )
    nav["nav"] = pd.to_numeric(
        nav["Net Asset Value"].str.replace(",", "", regex=False),
        errors="coerce",
    )

    nav = nav.dropna(subset=["date", "nav"])
    nav = nav[nav["nav"] > 0].copy()

    nav = nav.sort_values("date")

    # Overlapping date ranges may occur in downloaded files.
    duplicates = nav[nav.duplicated("date", keep=False)]

    if not duplicates.empty:
        print(
            f"Notice: {duplicates['date'].nunique()} NAV dates "
            "occur in multiple rows/files."
        )

        # Keep the last row for each date after sorting by source.
        nav = nav.drop_duplicates("date", keep="last")

    nav = nav[["date", "nav"]].sort_values("date").reset_index(drop=True)
    return nav


def read_benchmark_file() -> pd.DataFrame:
    """Read the NIFTY 50 TRI CSV and standardize its date/value columns."""
    if not BENCHMARK_FILES:
        raise FileNotFoundError(
            f"No benchmark CSV found in {BENCHMARK_DIR}"
        )

    if len(BENCHMARK_FILES) > 1:
        print(
            f"Found {len(BENCHMARK_FILES)} benchmark CSV files; "
            f"using {BENCHMARK_FILES[0].name}."
        )

    file_path = BENCHMARK_FILES[0]
    benchmark = pd.read_csv(file_path, encoding="utf-8-sig")
    benchmark.columns = benchmark.columns.str.strip()

    # Find the date column.
    date_column = next(
        (
            col for col in benchmark.columns
            if col.strip().lower() in {"date", "index date"}
        ),
        None,
    )

    if date_column is None:
        raise ValueError(
            f"Could not identify the date column in {file_path.name}. "
            f"Found columns: {list(benchmark.columns)}"
        )

    # Prefer Total Returns Index, not Net Total Return Index.
    value_column = next(
        (
            col for col in benchmark.columns
            if col.strip().lower() == "total returns index"
        ),
        None,
    )

    if value_column is None:
        raise ValueError(
            "Could not find a 'Total Returns Index' column. "
            f"Found columns: {list(benchmark.columns)}. "
            "Check the downloaded file before proceeding."
        )

    result = pd.DataFrame({
        "date": pd.to_datetime(
            benchmark[date_column],
            dayfirst=True,
            errors="coerce",
        ),
        "tri": pd.to_numeric(
            benchmark[value_column].astype(str).str.replace(
                ",", "", regex=False
            ),
            errors="coerce",
        ),
    })

    result = result.dropna(subset=["date", "tri"])
    result = result[result["tri"] > 0]
    result = result.sort_values("date")
    result = result.drop_duplicates("date", keep="last")
    result = result.reset_index(drop=True)

    return result


def build_aligned_data() -> pd.DataFrame:
    """Align NAV and TRI levels on common dates and calculate daily returns."""
    nav = read_nav_files()
    benchmark = read_benchmark_file()

    print(f"NAV observations: {len(nav)}")
    print(f"TRI observations: {len(benchmark)}")
    print(f"NAV date range: {nav['date'].min().date()} to "
          f"{nav['date'].max().date()}")
    print(f"TRI date range: {benchmark['date'].min().date()} to "
          f"{benchmark['date'].max().date()}")

    aligned = pd.merge(nav, benchmark, on="date", how="inner")
    aligned = aligned.sort_values("date").reset_index(drop=True)

    if aligned.empty:
        raise ValueError(
            "No common dates found between NAV and TRI. "
            "Check the date formats and file contents."
        )

    # Calculate returns only after matching dates.
    aligned["fund_return"] = aligned["nav"].pct_change()
    aligned["benchmark_return"] = aligned["tri"].pct_change()
    aligned["active_return"] = (
        aligned["fund_return"] - aligned["benchmark_return"]
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DIR / "aligned_daily_data.csv"
    aligned.to_csv(output_path, index=False)

    print(f"Common-date observations: {len(aligned)}")
    print(f"Common date range: {aligned['date'].min().date()} to "
          f"{aligned['date'].max().date()}")
    print(f"Saved aligned data to: {output_path}")

    return aligned


if __name__ == "__main__":
    data = build_aligned_data()
    print("\nFirst five aligned rows:")
    print(data.head().to_string(index=False))