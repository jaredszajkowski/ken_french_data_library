"""Regression tests pinning known values in the pulled Fama-French parquet files.

Ken French's data library is append-only for historical dates: the value for a
given (date, portfolio) pair never changes once published, but new dates are
appended over time. So every assertion here anchors on *early* fixed dates and
never on the last row.

Values are stored as decimals (raw percentages / 100), which introduces
floating-point representation error, so we compare with pytest.approx rather
than ==.

These tests read the parquet outputs produced by the `pull` step
(`python ./src/pull_fama_french_25_portfolios.py`, or `doit pull`). If the
`_data/` files are missing, the relevant tests are skipped.
"""

import pandas as pd
import pytest

import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

# Absolute tolerance for decimal returns. The source publishes 2 decimal places
# of a percentage (e.g. -0.46%), so 1e-9 comfortably absorbs float error while
# still catching any genuine change.
ABS_TOL = 1e-9

# Per-file expectations: the wide daily parquet each task_pull produces.
#   first_date  – the frozen first observation (anchors the whole series)
#   n_cols      – date column + 25 portfolios
#   anchors     – (date, portfolio, expected decimal value) golden values,
#                 spread across the 5x5 grid and two early dates.
FILE_CASES = {
    "french_portfolios_25_daily_size_and_bm": {
        "first_date": "1926-07-01",
        "n_cols": 26,
        "anchors": [
            ("1926-07-01", "SMALL LoBM", -0.0046),
            ("1926-07-01", "ME1 BM2", 0.0072),
            ("1926-07-01", "ME3 BM3", -0.0057),
            ("1926-07-01", "BIG HiBM", 0.0040),
            ("1926-07-02", "SMALL LoBM", 0.0057),
            ("1926-07-02", "BIG HiBM", 0.0024),
        ],
    },
    "french_portfolios_25_daily_size_and_op": {
        "first_date": "1963-07-01",
        "n_cols": 26,
        "anchors": [
            ("1963-07-01", "SMALL LoOP", -0.0070),
            ("1963-07-01", "ME1 OP2", -0.0098),
            ("1963-07-01", "ME3 OP3", -0.0077),
            ("1963-07-01", "BIG HiOP", -0.0070),
            ("1963-07-02", "SMALL LoOP", 0.0033),
            ("1963-07-02", "BIG HiOP", 0.0103),
        ],
    },
    "french_portfolios_25_daily_size_and_inv": {
        "first_date": "1963-07-01",
        "n_cols": 26,
        "anchors": [
            ("1963-07-01", "SMALL LoINV", -0.0067),
            ("1963-07-01", "ME1 INV2", -0.0055),
            ("1963-07-01", "ME3 INV3", -0.0044),
            ("1963-07-01", "BIG HiINV", -0.0048),
            ("1963-07-02", "SMALL LoINV", 0.0039),
            ("1963-07-02", "BIG HiINV", 0.0068),
        ],
    },
}


def _load(name):
    """Load a wide parquet by base name, skipping the test if it isn't built."""
    path = DATA_DIR / f"{name}.parquet"
    if not path.exists():
        pytest.skip(f"{path} not found; run `doit pull` first")
    return pd.read_parquet(path)


@pytest.mark.parametrize("name", list(FILE_CASES))
def test_structure(name):
    """Each file has the expected column count and frozen first date."""
    case = FILE_CASES[name]
    df = _load(name)

    assert "date" in df.columns
    assert df.shape[1] == case["n_cols"], (
        f"{name}: expected {case['n_cols']} columns, got {df.shape[1]}"
    )

    dates = pd.to_datetime(df["date"]).sort_values()
    assert dates.iloc[0] == pd.Timestamp(case["first_date"]), (
        f"{name}: first date {dates.iloc[0].date()} != {case['first_date']}"
    )
    # Every anchor column must exist.
    for _, portfolio, _ in case["anchors"]:
        assert portfolio in df.columns, f"{name}: missing column {portfolio!r}"


# Flatten anchors into one case per (file, date, portfolio) so a failure names
# the exact value that moved.
ANCHOR_CASES = [
    (name, date, portfolio, expected)
    for name, case in FILE_CASES.items()
    for date, portfolio, expected in case["anchors"]
]


@pytest.mark.parametrize(
    "name,date,portfolio,expected",
    ANCHOR_CASES,
    ids=[f"{n}-{d}-{p}" for n, d, p, _ in ANCHOR_CASES],
)
def test_anchor_value(name, date, portfolio, expected):
    """A known (date, portfolio) return matches its published value."""
    df = _load(name)
    df = df.set_index(pd.to_datetime(df["date"]))
    actual = df.loc[pd.Timestamp(date), portfolio]
    assert actual == pytest.approx(expected, abs=ABS_TOL), (
        f"{name}: ({date}, {portfolio}) = {actual!r}, expected ~{expected!r}"
    )
