# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: finm-32900-venv-p31211 (3.12.11.final.0)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Ken French Data Library - Fama-French 25 Portfolios

# %%
import warnings

import chartbook
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

warnings.filterwarnings("ignore")

# %% [markdown]
# ## Data Overview
#
# This pipeline downloads the Fama-French 25 portfolios from Ken French's Data
# Library and reshapes them into standardized FTSFR datasets. The portfolios are
# formed each year from the intersection of 5 size (market equity) quintiles and 5
# quintiles of a second characteristic, giving a 5x5 = 25 portfolio grid. Three
# daily datasets are written to `_data/`, each documented below:
# - `ftsfr_french_portfolios_25_daily_size_and_bm.parquet` — sorted by size and
#   book-to-market (value)
# - `ftsfr_french_portfolios_25_daily_size_and_op.parquet` — sorted by size and
#   operating profitability
# - `ftsfr_french_portfolios_25_daily_size_and_inv.parquet` — sorted by size and
#   investment
#
# Each file holds value-weighted daily returns in the FTSFR long format (one row
# per portfolio-date). The analysis below focuses on the size-and-book-to-market
# set and applies the same treatment to the others.
#
# Data source:
#
# - [Ken French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
#
# Reference:
#
# - Fama, Eugene F., and Kenneth R. French. "The cross-section of expected stock
#   returns." *The Journal of Finance* 47.2 (1992): 427-465.

# %% [markdown]
# ### Size x Book-to-Market (`ftsfr_french_portfolios_25_daily_size_and_bm.parquet`)
#
# Daily value-weighted returns for the 25 portfolios formed on size and
# book-to-market equity, reshaped into the standardized FTSFR schema: one row per
# (portfolio, date) with the return stacked into a single `y` column. This is the
# dataset used for the analysis in the rest of the notebook.
#
# | Variable | Description |
# |----------|-------------|
# | unique_id | Portfolio label — size quintile x B/M quintile (e.g. `SMALL LoBM`, `BIG HiBM`) |
# | ds | Observation date (daily) |
# | y | Daily value-weighted portfolio return (decimal) |

# %%
size_bm_df = pd.read_parquet(
    DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_bm.parquet"
)
print(f"Shape: {size_bm_df.shape}")
print(f"Columns: {size_bm_df.columns.tolist()}")
print(f"\nDate range: {size_bm_df['ds'].min()} to {size_bm_df['ds'].max()}")
print(f"Number of portfolios: {size_bm_df['unique_id'].nunique()}")
display(size_bm_df)

# %% [markdown]
# ### Size x Operating Profitability (`ftsfr_french_portfolios_25_daily_size_and_op.parquet`)
#
# Daily value-weighted returns for the 25 portfolios formed on size and operating
# profitability, in the same FTSFR long format.
#
# | Variable | Description |
# |----------|-------------|
# | unique_id | Portfolio label — size quintile x OP quintile (e.g. `SMALL LoOP`, `BIG HiOP`) |
# | ds | Observation date (daily) |
# | y | Daily value-weighted portfolio return (decimal) |

# %%
size_op_df = pd.read_parquet(
    DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_op.parquet"
)
print(f"Shape: {size_op_df.shape}")
print(f"Columns: {size_op_df.columns.tolist()}")
print(f"\nDate range: {size_op_df['ds'].min()} to {size_op_df['ds'].max()}")
print(f"Number of portfolios: {size_op_df['unique_id'].nunique()}")
display(size_op_df)

# %% [markdown]
# ### Size x Investment (`ftsfr_french_portfolios_25_daily_size_and_inv.parquet`)
#
# Daily value-weighted returns for the 25 portfolios formed on size and
# investment, in the same FTSFR long format.
#
# | Variable | Description |
# |----------|-------------|
# | unique_id | Portfolio label — size quintile x investment quintile (e.g. `SMALL LoINV`, `BIG HiINV`) |
# | ds | Observation date (daily) |
# | y | Daily value-weighted portfolio return (decimal) |

# %%
size_inv_df = pd.read_parquet(
    DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_inv.parquet"
)
print(f"Shape: {size_inv_df.shape}")
print(f"Columns: {size_inv_df.columns.tolist()}")
print(f"\nDate range: {size_inv_df['ds'].min()} to {size_inv_df['ds'].max()}")
print(f"Number of portfolios: {size_inv_df['unique_id'].nunique()}")
display(size_inv_df)

# %%
# Pivot the size-and-book-to-market set to wide format for analysis
size_bm_wide = size_bm_df.pivot(index="ds", columns="unique_id", values="y")
print(f"Wide format shape: {size_bm_wide.shape}")
print(f"Portfolios: {size_bm_wide.columns.tolist()}")

# %% [markdown]
# ## Summary Statistics
#
# Per-portfolio statistics for the size-and-book-to-market set. Daily means and
# standard deviations are annualized (252 trading days) and combined into a Sharpe
# ratio.

# %%
summary_stats = size_bm_wide.describe().T
summary_stats["annualized_mean"] = summary_stats["mean"] * 252
summary_stats["annualized_std"] = summary_stats["std"] * (252**0.5)
summary_stats["sharpe"] = (
    summary_stats["annualized_mean"] / summary_stats["annualized_std"]
)
display(
    summary_stats[
        ["count", "annualized_mean", "annualized_std", "sharpe", "min", "max"]
    ]
)

# %% [markdown]
# ## Data Coverage

# %%
print(f"Date range: {size_bm_wide.index.min()} to {size_bm_wide.index.max()}")
print(f"Number of trading days: {len(size_bm_wide)}")
print(f"Number of portfolios: {len(size_bm_wide.columns)}")
print(f"Missing values per portfolio:")
print(size_bm_wide.isnull().sum())

# %% [markdown]
# ## Cumulative Returns
#
# Cumulative growth of the four corner portfolios (small/big size x low/high B/M),
# plotted on a log scale.

# %%
corner_portfolios = ["SMALL LoBM", "SMALL HiBM", "BIG LoBM", "BIG HiBM"]
available_corners = [p for p in corner_portfolios if p in size_bm_wide.columns]

fig, ax = plt.subplots(figsize=(14, 6))
for portfolio in available_corners:
    cumret = (1 + size_bm_wide[portfolio]).cumprod()
    ax.plot(cumret.index, cumret.values, label=portfolio, linewidth=0.8)

ax.set_title("Cumulative Returns: Corner Portfolios (Size x B/M)", fontsize=14)
ax.set_xlabel("Date")
ax.set_ylabel("Cumulative Return (Starting at 1)")
ax.legend(loc="upper left")
ax.grid(True, alpha=0.3)
ax.set_yscale("log")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Correlation Matrix
#
# Correlation of daily returns across a subset of the size-and-book-to-market
# portfolios.

# %%
n_portfolios = min(10, len(size_bm_wide.columns))
subset_cols = size_bm_wide.columns[:n_portfolios]
corr_matrix = size_bm_wide[subset_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(
    corr_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    square=True,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8},
    annot_kws={"size": 8},
)
plt.title("Correlation Matrix: Fama-French Portfolios (Size x B/M)", fontsize=12)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Distribution of Daily Returns
#
# Histograms of daily returns for the first four portfolios, with the mean marked.

# %%
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

portfolios_to_plot = size_bm_wide.columns[:4].tolist()
for i, portfolio in enumerate(portfolios_to_plot):
    ax = axes[i]
    size_bm_wide[portfolio].hist(ax=ax, bins=100, edgecolor="black", alpha=0.7)
    mean_ret = size_bm_wide[portfolio].mean()
    ax.axvline(mean_ret, color="red", linestyle="--", label=f"Mean: {mean_ret:.4f}")
    ax.set_title(f"{portfolio}", fontsize=10)
    ax.set_xlabel("Daily Return")
    ax.set_ylabel("Frequency")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.suptitle("Distribution of Daily Returns", y=1.02, fontsize=14)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Summary
#
# This dataset provides daily value-weighted returns for the Fama-French 25
# portfolios formed on size and book-to-market, operating profitability, and
# investment. These portfolios are widely used as test assets in empirical asset
# pricing research to evaluate factor models and understand the cross-section of
# expected returns.
#
# Key applications:
#
# - Factor model estimation and testing (e.g. the three- and five-factor models)
# - Studying the size, value, profitability, and investment premiums
# - Cross-sectional asset pricing and portfolio sorting
# - Benchmark test assets for empirical finance research
