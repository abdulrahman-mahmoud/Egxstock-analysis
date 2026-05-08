# EGX Stock Analysis

This repository is a Python-based EGX stock analysis project built around a Streamlit dashboard, local CSV datasets, scraping utilities, and notebook-based exploration.

It documents a practical workflow for:

- collecting historical EGX stock data from Yahoo Finance
- scraping company snapshot data from African Markets
- experimenting with live quote scraping from Mubasher
- cleaning and aligning market datasets
- calculating returns, volatility, sector growth, and summary metrics
- visualizing results through charts, network graphs, and a dashboard

## Overview

The codebase is centered on the Egyptian Exchange (EGX). It combines a small app layer in `app/`, stored datasets in `data/`, notebook work in `Proessing/`, and bundled PDF reports in `data/pdf/`.

The main shipped interface is a Streamlit dashboard in [GuiMaking.py](/d:/Projects/Egy%20stock%20egyx33/Egxstock-analysis/app/GuiMaking.py). That dashboard loads the local CSV files, lets the user refresh parts of the data through scraping, and presents charts for company-level, sector-level, and market-level analysis.

## What We Used

### Libraries

The project currently uses these libraries from [requirements.txt](/d:/Projects/Egy%20stock%20egyx33/Egxstock-analysis/requirements.txt):

- `pandas`
- `numpy`
- `streamlit`
- `plotly`
- `matplotlib`
- `networkx`
- `seaborn`
- `yfinance`
- `requests`
- `beautifulsoup4`
- `selenium`
- `ipykernel`

### Data Sources

The data sources referenced in the Python files and notebooks are:

- `Yahoo Finance` through `yfinance` for historical EGX stock price data
- `African Markets` for company, sector, YTD, and market cap snapshot data
- `Mubasher` for live quote scraping experiments

### Tools and Runtime Dependencies

- `Streamlit` powers the main dashboard UI
- `Plotly` is used for interactive line charts inside the dashboard
- `Matplotlib`, `Seaborn`, and `NetworkX` are used for static analysis and plotting
- `Selenium` is used for dynamic scraping and requires a working Chrome / Chromedriver setup
- `Jupyter notebooks` in `Proessing/` capture the exploratory and academic workflow behind the app

## Repository Structure

```text
Egxstock-analysis/
+-- app/
|   +-- analyzer.py
|   +-- scraper.py
|   +-- GuiMaking.py
|   +-- vizulliztion.py
+-- data/
|   +-- raw.csv
|   +-- stock_data.csv
|   +-- pdf/
|       +-- EGX Stock Market - Data Acquisition.pdf
|       +-- EGX Stock Market- Journey Report.pdf
+-- Proessing/
|   +-- cleaning_analysis.ipynb
|   +-- scrapers/
|       +-- api_fetcher.ipynb
|       +-- Bs4.ipynb
|       +-- SeleniumProject.ipynb
+-- requirements.txt
+-- README.md
```

## Core Modules

### `app/GuiMaking.py`

This is the main Streamlit entrypoint. It loads the analyzer, visualization, and scraper classes, then exposes these dashboard pages:

- `Overview`
- `Scraping`
- `Company Analysis`
- `Network Analysis`
- `Gainers & Losers`
- `Sector Analysis`
- `3D Analysis`
- `Summary`

### `app/analyzer.py`

`EgxAnalyzer` handles the main data logic:

- loads `data/raw.csv` and `data/stock_data.csv`
- cleans dates and numeric fields
- aligns company names across sources
- builds sector mappings and fallback metadata
- calculates daily returns, total gain, rolling volatility, and portfolio growth
- prepares monthly performance, gainers/losers, sector growth, and summary-page metrics

### `app/scraper.py`

`EgxScraper` provides three data collection paths:

- `api(start_date, end_date)` downloads historical stock data with `yfinance`
- `african_markets_scraper()` uses Selenium to scrape listed company data from African Markets
- `mubasher_live_quotes()` uses `requests` and `BeautifulSoup` to parse live quote rows from Mubasher

It also includes helpers to save and load CSV files.

### `app/vizulliztion.py`

`EgxVisualization` builds the charts used by the app:

- sector network graph
- annualized volatility bar chart
- sector growth chart
- rolling volatility line chart
- monthly return heatmap
- top gainers and top losers charts
- 3D monthly return scatter plot

## Data Files

The repository already includes two CSV datasets used by the dashboard.

### `data/raw.csv`

File: [raw.csv](/data/raw.csv)

Purpose:
- historical OHLCV-style stock data used for most of the analysis views

Observed columns:
- `Company`
- `Symbol`
- `Date`
- `Open`
- `High`
- `Low`
- `Close`
- `Adj Close`
- `Volume`

Current repo snapshot:
- 2449 rows
- 9 columns

### `data/stock_data.csv`

File: [stock_data.csv](/data/stock_data.csv)

Purpose:
- company-level market snapshot data used to attach sector, price, YTD, and market cap metadata

Observed columns:
- `Company`
- `Sector`
- `Price`
- `1D`
- `YTD`
- `M.Cap`
- `Date`

Current repo snapshot:
- 317 rows
- 7 columns

Current quirk:
- the file contains a duplicated header row as the first data row, so anyone inspecting the raw CSV directly should expect to see `Company,Sector,Price,1D,YTD,M.Cap,Date` repeated once inside the data body

## Notebooks And Reports

### Notebooks in `Proessing/`

The `Proessing/` folder contains notebook work that appears to support the app and document the project workflow.

- [cleaning_analysis.ipynb](/Proessing/cleaning_analysis.ipynb): main cleaning and analysis notebook
- [api_fetcher.ipynb](//Proessing/scrapers/api_fetcher.ipynb): Yahoo Finance data collection notebook
- [Bs4.ipynb](//Proessing/scrapers/Bs4.ipynb): BeautifulSoup scraping experiment for Mubasher
- [SeleniumProject.ipynb](/Proessing/scrapers/SeleniumProject.ipynb): Selenium scraping experiment

### Reports in `data/pdf/`

Supporting PDFs are included here:

- [EGX Stock Market - Data Acquisition.pdf](/data/pdf/EGX%20Stock%20Market%20-%20Data%20Acquisition.pdf)
- [EGX Stock Market- Journey Report.pdf](/data/pdf/EGX%20Stock%20Market-%20Journey%20Report.pdf)

## Installation

Windows-friendly setup from the repository root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run The App

Start the Streamlit dashboard from the repository root:

```bash
streamlit run app/GuiMaking.py
```

## Data Refresh Workflow

To rebuild the shipped CSV files through the dashboard:

1. Run the Streamlit app.
2. Open the `Scraping` page.
3. Choose the desired start and end dates.
4. Click `Yahoo Finance API` to refresh `data/raw.csv`.
5. Click `African Markets Scraper` to refresh `data/stock_data.csv`.

## Notes / Known Constraints

- The README keeps the existing repo names exactly as they appear, including `Proessing`, `GuiMaking.py`, and `vizulliztion.py`.
- The dashboard expects both `data/raw.csv` and `data/stock_data.csv` to exist before most analysis pages can load.
- `african_markets_scraper()` depends on Selenium plus a working Chrome / Chromedriver environment.
- `mubasher_live_quotes()` exists in the scraper module, but the main dashboard flow currently saves historical Yahoo data and African Markets snapshot data, not Mubasher output.
- `app/analyzer.py` includes name-mapping and fallback metadata logic to reconcile companies across the available datasets.

## Authors

The notebooks identify the project authors as:

- Abdel-Rahman Mahmoud Atai
- Omar Saeed Abouzeed
