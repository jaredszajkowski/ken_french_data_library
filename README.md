# Ken French Data Library Pipeline

A `doit`-driven data pipeline that downloads the Fama-French 25 portfolios from
Ken French's Data Library and reshapes them into standardized "ftsfr" datasets.
It is one of several sibling pipelines split out of the former `ftsfr` monorepo,
each self-contained with the same `dodo.py` / `src/` / `chartbook.toml` shape.

## Data Source

The data is publicly available from
[Ken French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).
No credentials or `.env` are required — the source data is public.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the full pipeline:
   ```bash
   doit
   ```

   Other useful commands:
   ```bash
   doit list             # show tasks
   doit <task>           # run one task (see Pipeline below)
   doit forget && doit   # rebuild ignoring cached state (state lives in .doit.db)
   ```

3. View the generated documentation in `docs/index.html`.

To debug a single step, run its script directly, e.g.
`python ./src/pull_fama_french_25_portfolios.py`.

## Pipeline

`dodo.py` defines the DAG. Data flows through two gitignored directories created
by `task_config`: `_data/` (parquet outputs) and `_output/` (executed notebooks
and chart HTML). The tasks run in dependency order:

1. **config** — create the `_data/` and `_output/` directories.
2. **pull** (`src/pull_fama_french_25_portfolios.py`) — download and unzip the
   Ken French CSVs, parse the multi-section layout, convert percentages to
   decimals, and write **wide** parquet (one column per portfolio, plus `date`).
3. **format** (`src/create_ftsfr_datasets.py`) — reshape wide → **long** and
   write the `ftsfr_*.parquet` files.
4. **run_notebooks** — convert `src/summary_ken_french_ipynb.py` (a jupytext
   percent-format script) to a notebook, execute it, and export HTML.
5. **generate_charts** (`src/generate_chart.py`) — write standalone Plotly HTML
   charts to `_output/`.
6. **generate_pipeline_site** — run `chartbook build -f` to produce
   `docs/index.html` from `chartbook.toml`.

## Outputs

The standardized `ftsfr_*.parquet` datasets (long format):

- `ftsfr_french_portfolios_25_daily_size_and_bm.parquet` — Daily 25 portfolios sorted by Size and Book-to-Market
- `ftsfr_french_portfolios_25_daily_size_and_op.parquet` — Daily 25 portfolios sorted by Size and Operating Profitability
- `ftsfr_french_portfolios_25_daily_size_and_inv.parquet` — Daily 25 portfolios sorted by Size and Investment

### ftsfr long format

Every `ftsfr_*.parquet` file has exactly three columns:

- `unique_id` — portfolio name (e.g. `SMALL LoBM`)
- `ds` — date
- `y` — value

`convert_wide_to_long_format` in `src/create_ftsfr_datasets.py` is the canonical
transform. Sibling pipelines and `chartbook.toml` (`date_col = "ds"`) rely on
this contract.

## Portfolio Construction

The portfolios are formed on the intersection of:

- **Size**: Market equity (5 quintiles)
- **Characteristic**: Book-to-Market, Operating Profitability, or Investment (5 quintiles)

This creates 5×5 = 25 portfolios for each characteristic combination.

## Academic References

### Primary Papers

- **Fama and French (1992)** — "The cross-section of expected stock returns"
  - The Journal of Finance 47.2 (1992): 427-465

- **Fama and French (1993)** — "Common risk factors in the returns on stocks and bonds"
  - Journal of Financial Economics 33 (1993): 3-56
  - Foundational work on size and value factors

### Key Findings

- Size (SMB) and value (HML) factors capture significant cross-sectional variation in stock returns
- The 25 portfolios provide test assets for evaluating asset pricing models
