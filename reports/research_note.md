# Passive Fund Tracking Stress & Benchmark Drift Analysis

**Research note**  
**Study period:** 24 October 2025 – 22 October 2026  
**Fund:** Kotak Nifty 50 Index Fund — Direct Plan — Growth  
**Benchmark:** NIFTY 50 Total Returns Index (TRI)

## 1. Research question

How closely does the selected index fund track its benchmark, and when does the variability of its daily active returns become unusually elevated?

The analysis measures the difference between fund and benchmark returns and examines whether elevated rolling tracking error occurs in identifiable episodes.

## 2. Data and methodology

Fund NAV observations were collected from AMFI NAV data files. Benchmark levels were taken from the downloaded historical NIFTY 50 TRI dataset. Both series were aligned by date using an inner join, retaining only dates available in both datasets.

Daily simple returns were calculated from consecutive aligned NAV and TRI observations. Daily active return was defined as the fund return minus the benchmark return.

Annualized tracking error was calculated as the sample standard deviation of daily active returns multiplied by the square root of 252. The information ratio was calculated as mean daily active return multiplied by 252, divided by annualized tracking error.

A 60-observation rolling tracking-error series was used to identify periods of elevated variability. Observations above the 95th percentile of the available rolling tracking-error values were flagged retrospectively. Consecutive flagged observations were grouped into episodes.

## 3. Results

The aligned dataset contains 245 common-date observations and 244 valid daily return observations.

| Metric | Result |
|---|---:|
| Fund cumulative return | -11.1752% |
| Benchmark cumulative return | -11.0916% |
| Cumulative return gap | -0.0836 percentage points |
| Annualized tracking error | 0.057268% |
| Information ratio | -1.729851 |
| Elevated rolling tracking-error observations | 10 |
| Identified elevated-error episodes | 5 |

The fund's cumulative return was approximately 0.0836 percentage points below the benchmark over the study period. The negative information ratio indicates that average active return was negative relative to the estimated variability of active returns under the selected annualization convention.

The retrospective threshold identified ten elevated rolling tracking-error observations, grouped into five episodes. These flags indicate periods of relatively high tracking-error variability within this sample; they do not establish that the deviations were economically material or caused by a particular fund-management decision.

## 4. Data validation

Automated checks found no duplicate dates in the filtered NAV series, benchmark series, or aligned dataset. Source levels matched the corresponding aligned levels, and stored daily returns matched returns recalculated from the aligned series.

Compounded daily returns also reconciled with the first-to-last level returns for both the fund and benchmark.

These checks establish computational consistency with the downloaded files. They do not independently establish the provenance, completeness, or official status of the downloaded benchmark data.

## 5. Interpretation and limitations

The observed cumulative return gap was small relative to the absolute cumulative movements of the fund and benchmark. Tracking error measures the variability of active returns; it is not the same as cumulative underperformance.

The 95th-percentile threshold is sample-dependent and retrospective. It should not be interpreted as a regulatory limit, a forward-looking risk forecast, or proof of a fund tracking failure.

The analysis does not identify causal drivers such as expenses, cash balances, corporate-action handling, execution costs, or index-rebalancing effects. Such explanations would require additional evidence and separate tests.

The findings also depend on the selected date alignment, source-data accuracy, simple-return convention, 252-day annualization assumption, and 60-observation rolling window.

## 6. Conclusion and next steps

This project implements a reproducible framework for measuring benchmark-relative performance and identifying periods of elevated tracking-error variability.

Before drawing stronger conclusions, the benchmark file's provenance and TRI definition should be confirmed against the official source. Further work could include sensitivity analysis across rolling-window lengths, comparison with a second index fund tracking the same benchmark, and investigation of specific flagged dates using independently verified market and fund disclosures.

The current results are descriptive and should not be interpreted as evidence of a specific cause of tracking deviations.
