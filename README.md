# EGX Stocks & Currency Data Acquisition

> A modular Python framework for acquiring, processing, and visualizing financial data from the **Egyptian Exchange (EGX)** — built for academic research and practical finance applications.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Visualizations](#visualizations)
- [GUI Dashboard](#gui-dashboard)
- [Requirements](#requirements)
- [Notes](#notes)

---

## Overview

This project provides end-to-end tooling for EGX market data: scraping live stock prices and currency rates, cleaning and structuring the data, modeling relationships via graph analysis, and presenting insights through heatmaps, 3D point clouds, and an interactive desktop dashboard.

It was developed as a two-phase academic project and is designed to be **scalable**, **reusable**, and easy to extend.

---

## Features

### Data Collection
| Method | Source | Purpose |
|---|---|---|
| `BeautifulSoup` | `mubasher.info` | Live stock prices, EGX indices, sector data, company fundamentals |
| `Selenium` | `stockanalysis.com` | Full ticker list, per-stock financials, market cap data |
| `Selenium` | `african-markets.com` | EGX30 index history, weekly summaries, listed companies |
| `yfinance` | Yahoo Finance | Historical OHLCV data for EGX-listed tickers (`.CA` suffix) |
| `SerpApi` | Google Finance | Fallback — stock price, movement, and news via search |

### Data Processing
- **Cleaning & normalization** of raw scraped data (handling missing values, type casting, deduplication)
- **Graph construction** via `NetworkX` — models co-traded stocks, sector relationships, and currency correlations

### Visualization & Insights
- **Network graphs** — identify key stocks (high-degree nodes) and sector communities via community detection
- **Heatmaps** — pricing trends across sectors, currency fluctuation over time
- **3D Point Cloud** — clustering of stocks by price, volume, and performance metrics

### GUI Dashboard
- Built with `Tkinter`, organized across **7 tabs**
- Covers: live data view, historical charts, network graph explorer, heatmap viewer, point cloud, sector breakdown, and settings
- Threaded data fetching to keep the UI responsive

---

## Project Structure

```
egx-data-acquisition/
│
├── data/
│   ├── raw/                  # Raw scraped output (CSV, JSON)
│   └── processed/            # Cleaned and normalized datasets
│
├── scrapers/
│   ├── bs4_scraper.py        # BeautifulSoup-based scraper
│   ├── selenium_scraper.py   # Selenium scraper for dynamic content
│   └── api_fetcher.py        # yfinance + SerpApi + REST integrations
│
├── processing/
│   ├── cleaner.py            # Data cleaning and normalization
│   └── graph_builder.py      # NetworkX graph construction
│
├── visualization/
│   ├── network_viz.py        # Network graph plots and community detection
│   ├── heatmap.py            # Seaborn/Matplotlib heatmaps
│   └── point_cloud.py        # 3D scatter / point cloud analysis
│
├── gui/
│   └── dashboard.py          # Tkinter 7-tab dashboard (main entry point)
│
├── requirements.txt
├── .env.example              # API key template
└── README.md
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/egx-data-acquisition.git
cd egx-data-acquisition

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and add your SerpApi key and any other credentials
```

---

## Usage

### Launch the GUI Dashboard
```bash
python gui/dashboard.py
```

### Run scrapers individually
```bash
# Static scraper (BeautifulSoup)
python scrapers/bs4_scraper.py

# Dynamic scraper (Selenium) — requires ChromeDriver
python scrapers/selenium_scraper.py

# Fetch historical data via yfinance / APIs
python scrapers/api_fetcher.py
```

### Generate visualizations
```bash
python visualization/network_viz.py
python visualization/heatmap.py
python visualization/point_cloud.py
```

---

## Data Sources

| Source | Tool | Data |
|---|---|---|
| [Mubasher](https://english.mubasher.info/markets/EGX/) | `BeautifulSoup` | Live stock prices, EGX30 & EGX33 indices, sector breakdowns, company fundamentals |
| [Stock Analysis](https://stockanalysis.com/list/egyptian-stock-exchange/) | `Selenium` | Full EGX ticker list, market cap, per-stock financials and historical data |
| [African Markets](https://african-markets.com/en/stock-markets/egx) | `Selenium` | EGX30 performance, index history, weekly market summaries, listed companies |
| [SerpApi](https://serpapi.com/) | API | Google Finance results for EGX stocks — price, movement, news (fallback) |
| [yfinance](https://pypi.org/project/yfinance/) | API | Historical OHLCV for EGX-listed tickers (use `.CA` suffix e.g. `COMI.CA`) |

> **Note:** SerpApi requires an API key. See `.env.example` for the required variables. All scraping targets are non-government, publicly accessible sources with no heavy bot protection.

---

## Visualizations

### Network Graph
Models relationships between stocks — edges represent co-trading activity or sector membership. Community detection highlights clusters of related equities.

### Heatmap
Displays price movements or currency fluctuations across time and sector dimensions, built with `seaborn` on a `pandas` pivot table.

### 3D Point Cloud
Plots each stock as a point in (price, volume, % change) space. K-Means clustering is applied to reveal performance groupings.

---

## GUI Dashboard

The `Tkinter` dashboard exposes all project outputs in a single window across 7 tabs:

| Tab | Content |
|---|---|
| Live Data | Real-time stock and currency snapshot |
| Historical | OHLCV chart for any selected ticker |
| Network | Interactive graph explorer |
| Heatmap | Sector × time heatmap |
| Point Cloud | 3D stock clustering |
| Sectors | Breakdown by EGX sector category |
| Settings | Scraper config, API key management |

Data fetching runs on background threads so the interface stays responsive during live updates.

---

## Requirements

```
beautifulsoup4
selenium
yfinance
google-search-results   # SerpApi
networkx
pandas
numpy
matplotlib
seaborn
requests
python-dotenv
```

Install all at once:
```bash
pip install -r requirements.txt
```

> **ChromeDriver** is required for Selenium. Download the version matching your Chrome install from [chromedriver.chromium.org](https://chromedriver.chromium.org/downloads) and add it to your PATH.

---

## Notes

- Data availability depends on EGX site structure — scraper selectors may need updating if the site changes.
- `yfinance` ticker symbols for EGX stocks follow the format `XXXX.CA` (e.g. `COMI.CA` for CIB).
- This project was built and tested on Python 3.10+.

---

*Built as part of a university data acquisition and visualization course — Egyptian Exchange focus, Phase 1 & 2.*
