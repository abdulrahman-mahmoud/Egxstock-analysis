import os
import time
import logging
import requests
import yfinance as yf
import pandas as pd

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from app.constants import CompaniesNamesStock, CompanySectorsStock

logging.getLogger("yfinance").setLevel(logging.ERROR)


class EgxScraper:



    def __init__(self):

        self.file = pd.DataFrame()

        self.live_quotes = pd.DataFrame()

        self.african_markets = pd.DataFrame()
        self.CompaniesNamesStock = CompaniesNamesStock
        self.CompanySectorsStock = CompanySectorsStock

    # ==========================================
    # Yahoo Finance Historical Data
    # ==========================================
    def api(self, start_date, end_date):
        symbols = list(self.CompaniesNamesStock.keys())
        allData = []

        for symbol in symbols:

            try:

                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    auto_adjust=False,
                    actions=False,
                )

                if df.empty:
                    print(f"{symbol} skipped")
                    continue

                df.reset_index(inplace=True)

                df.insert(
                    0,
                    "Company",
                    self.CompaniesNamesStock[symbol]
                )

                df.insert(
                    1,
                    "Symbol",
                    symbol
                )

                df.insert(
                    2,
                    "Sector",
                    self.CompanySectorsStock.get(symbol, "Unknown")
                )

                allData.append(df)

                print(f"{symbol} loaded")

            except Exception as e:

                print(f"{symbol} -> {e}")

        if len(allData) == 0:

            print("No data collected")
            return pd.DataFrame()

        self.file = pd.concat(
            allData,
            ignore_index=True
        )

        return self.file

    # ==========================================
    # African Markets (Selenium)
    # ==========================================
    def african_markets_scraper(self):

        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = None

        try:

            driver = webdriver.Chrome(
                options=options
            )

            url = "https://www.african-markets.com/en/stock-markets/egx/listed-companies"

            driver.get(url)

            time.sleep(5)

            rows = driver.find_elements(
                By.TAG_NAME,
                "tr"
            )

            data = []

            for row in rows:

                cells = row.find_elements(
                    By.TAG_NAME,
                    "td"
                )

                if len(cells) >= 7:

                    row_data = [
                        cell.text.strip()
                        for cell in cells[:7]
                    ]

                    data.append(row_data)

            columns = [
                "Company",
                "Sector",
                "Price",
                "1D",
                "YTD",
                "M.Cap",
                "Date"
            ]

            self.african_markets = pd.DataFrame(
                data,
                columns=columns
            )

            return self.african_markets

        except Exception as e:

            print(f"Selenium Error -> {e}")

            return pd.DataFrame()

        finally:

            if driver is not None:
                driver.quit()

    # ==========================================
    # Save CSV
    # ==========================================
    def save_csv(self, df, path):

        if df.empty:

            print("No data to save")
            return

        os.makedirs(
            os.path.dirname(path),
            exist_ok=True
        )

        df.to_csv(
            path,
            index=False
        )

        print(f"Saved -> {path}")

    # ==========================================
    # Load CSV
    # ==========================================
    def load_csv(self, path):

        return pd.read_csv(path)
