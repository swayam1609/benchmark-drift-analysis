# Passive Fund Tracking Stress & Benchmark Drift Analysis

## Project objective
Evaluate how closely Kotak Nifty 50 Index Fund — Direct Plan — Growth tracks the NIFTY 50 Total Returns Index (TRI), and identify periods when tracking error becomes unusually elevated.

## Analysis period
24 October 2025 – 22 October 2026

## Data
- Fund: Kotak Nifty 50 Index Fund — Direct Plan — Growth
- Scheme code: 148978
- ISIN: INF174KA1HA7
- Benchmark: NIFTY 50 Total Returns Index (TRI)
- Fund NAV data: AMFI NAV files
- Benchmark data: downloaded historical TRI data

## Preliminary findings
- Fund cumulative return: -11.1752%
- Benchmark cumulative return: -11.0916%
- Cumulative return gap: -0.0836 percentage points
- Annualized tracking error: 0.057268%
- Information ratio: -1.729851
- Elevated rolling tracking-error observations: 10
- Identified elevated-error episodes: 5

## Data validation
- Source-level comparisons: passed
- Daily-return recalculation checks: passed
- Cumulative-return reconciliation: passed
- Duplicate aligned dates: none

## Interpretation and limitations
The fund's cumulative return was slightly below the benchmark over the observed period. The calculated annualized tracking error indicates the variability of daily active returns under the methodology implemented in this project.

Elevated tracking-error periods are identified retrospectively using the 95th percentile of observed rolling tracking error. They are statistical flags, not proof of a specific operational failure or its cause.

The results depend on the correctness and consistency of the downloaded source data, the selected benchmark series, and the implemented return methodology. The analysis does not establish that expenses, cash holdings, transaction costs, or any other individual factor caused a deviation.

## Reproducibility
Run the complete analysis from the project root:

`python main.py`

Run the automated tests:

`python -m pytest -v`

Generate the Excel report:

`python -m src.excel_report`

Generate the data validation report:

`python -m src.validate_data`