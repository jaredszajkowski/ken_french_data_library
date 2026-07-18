import os
import platform
import sys
from pathlib import Path

import chartbook

sys.path.insert(1, "./src/")

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
OUTPUT_DIR = BASE_DIR / "_output"
OS_TYPE = "nix" if platform.system() != "Windows" else "windows"


## Helpers for handling Jupyter Notebook tasks
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"


## Helper functions for automatic execution of Jupyter notebooks
# fmt: off
def jupyter_execute_notebook(notebook_path):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --inplace '{notebook_path}'"
def jupyter_to_html(notebook_path, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --output-dir='{output_dir}' '{notebook_path}'"
def jupyter_to_md(notebook_path, output_dir=OUTPUT_DIR):
    """Requires jupytext"""
    return f"jupytext --to markdown --output-dir='{output_dir}' '{notebook_path}'"
def jupyter_to_python(notebook_path, notebook, build_dir):
    """Convert a notebook to a python script"""
    return f"jupyter nbconvert --to python '{notebook_path}' --output _{notebook}.py --output-dir '{build_dir}'"
def jupyter_clear_output(notebook_path):
    """Clear the output of a notebook"""
    return f"jupyter nbconvert --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace '{notebook_path}'"
# fmt: on


def mv(from_path, to_path):
    """Copy a notebook to a folder"""
    from_path = Path(from_path)
    to_path = Path(to_path)
    to_path.mkdir(parents=True, exist_ok=True)
    if OS_TYPE == "nix":
        command = f"mv '{from_path}' '{to_path}'"
    else:
        command = f"move '{from_path}' '{to_path}'"
    return command


##################################
## Begin rest of PyDoit tasks here
##################################


def task_config():
    """Create empty directories for data and output if they don't exist"""
    def create_dirs():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "actions": [create_dirs],
        "targets": [DATA_DIR, OUTPUT_DIR],
        "verbosity": 2,
    }


def task_pull():
    """Pull Fama-French portfolio data"""
    return {
        "actions": [
            f"python ./src/pull_fama_french_25_portfolios.py",
        ],
        "targets": [
            DATA_DIR / "french_portfolios_25_daily_size_and_bm.parquet",
            DATA_DIR / "french_portfolios_25_daily_size_and_op.parquet",
            DATA_DIR / "french_portfolios_25_daily_size_and_inv.parquet",
        ],
        "file_dep": [
            f"./src/pull_fama_french_25_portfolios.py",
        ],
        "clean": [],
    }


def task_format():
    """Format data into standardized FTSFR datasets"""
    return {
        "actions": [
            f"python ./src/create_ftsfr_datasets.py",
        ],
        "targets": [
            DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_bm.parquet",
            DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_op.parquet",
            DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_inv.parquet",
        ],
        "file_dep": [
            f"./src/create_ftsfr_datasets.py",
            DATA_DIR / "french_portfolios_25_daily_size_and_bm.parquet",
            DATA_DIR / "french_portfolios_25_daily_size_and_op.parquet",
            DATA_DIR / "french_portfolios_25_daily_size_and_inv.parquet",
        ],
        "clean": [],
    }


def task_tests():
    """Run the pytest suite (golden-value checks against the pulled data)."""
    return {
        "actions": ["python -m pytest ./src/test_parquet_values.py -v"],
        "file_dep": [
            "./src/test_parquet_values.py",
            "./src/pull_fama_french_25_portfolios.py",
            DATA_DIR / "french_portfolios_25_daily_size_and_bm.parquet",
            DATA_DIR / "french_portfolios_25_daily_size_and_op.parquet",
            DATA_DIR / "french_portfolios_25_daily_size_and_inv.parquet",
        ],
        "task_dep": ["pull"],
        "verbosity": 2,
        "uptodate": [False],
    }


notebook_tasks = {
    "summary_ken_french_ipynb": {
        "path": "./src/summary_ken_french_ipynb.py",
        "file_dep": [
            DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_bm.parquet",
        ],
        "targets": [],
    },
}
notebook_files = []
for notebook in notebook_tasks.keys():
    pyfile_path = Path(notebook_tasks[notebook]["path"])
    notebook_files.append(pyfile_path)


# fmt: off
def task_run_notebooks():
    """Preps the notebooks for presentation format.
    Execute notebooks if the script version of it has been changed.
    """

    for notebook in notebook_tasks.keys():
        pyfile_path = Path(notebook_tasks[notebook]["path"])
        notebook_path = pyfile_path.with_suffix(".ipynb")
        yield {
            "name": notebook,
            "actions": [
                f"jupytext --to notebook --output {notebook_path} {pyfile_path}",
                jupyter_execute_notebook(notebook_path),
                jupyter_to_html(notebook_path),
                mv(notebook_path, OUTPUT_DIR),
            ],
            "task_dep": ["tests"],
            "file_dep": [
                pyfile_path,
                *notebook_tasks[notebook]["file_dep"],
            ],
            "targets": [
                OUTPUT_DIR / f"{notebook}.html",
                *notebook_tasks[notebook]["targets"],
            ],
            "clean": True,
        }
# fmt: on


def task_generate_charts():
    """Generate interactive HTML charts."""
    return {
        "actions": ["python src/generate_chart.py"],
        "file_dep": [
            "src/generate_chart.py",
            DATA_DIR / "ftsfr_french_portfolios_25_daily_size_and_bm.parquet",
        ],
        "targets": [
            OUTPUT_DIR / "french_portfolios_replication.html",
            OUTPUT_DIR / "french_portfolios_cumulative_returns.html",
        ],
        "verbosity": 2,
        "task_dep": ["format", "tests"],
    }


def task_generate_pipeline_site():
    return {
        "actions": [
            "chartbook build -f",
        ],
        "targets": ["docs/index.html"],
        "file_dep": [
            "chartbook.toml",
            *notebook_files,
            OUTPUT_DIR / "french_portfolios_replication.html",
            OUTPUT_DIR / "french_portfolios_cumulative_returns.html",
        ],
        "task_dep": ["run_notebooks", "generate_charts"],
    }
