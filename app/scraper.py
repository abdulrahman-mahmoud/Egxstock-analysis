import os
import time
import requests
import yfinance as yf
import pandas as pd

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class EgxScraper:

    CompaniesNamesStock = {
        "SWDY.CA": "El Sewedy Electric",
        "CLHO.CA": "Cleopatra Hospital",
        "ISPH.CA": "Ibnsina Pharma",
        "AMOC.CA": "Alexandria Mineral Oils",
        "PHDC.CA": "Palm Hills Developments",
        "OCDI.CA": "Orascom Construction",
        "ETEL.CA": "Telecom Egypt",
        "HELI.CA": "Heliopolis Housing",
        "SKPC.CA": "Sidi Kerir Petrochemicals",
        "SUGR.CA": "Delta Sugar",
        "TMGH.CA": "Talaat Moustafa Group",
        "FWRY.CA": "Fawry",
        "EGTS.CA": "Egyptian Transport & Commercial Services",
        "IRON.CA": "Egyptian Iron & Steel",
        "JUFO.CA": "Juhayna Food Industries",
        "ELEC.CA": "Egyptian Electrical Cables",
        "LCSW.CA": "Lecico Egypt",
        "MTIE.CA": "Modern Furniture",
        "MFPC.CA": "Misr Fertilizers Production Company",
        "ORWE.CA": "Orascom Telecom Media & Technology",
        "ACGC.CA": "Alexandria Container & Cargo Handling",
        "ABUK.CA": "Abu Kir Fertilizers",
        "HDBK.CA": "Housing & Development Bank",
        "POUL.CA": "Cairo Poultry (Koki)",
        "RAYA.CA": "Raya Holding",
        "MCQE.CA": "Misr Capital",
        "UNIT.CA": "Unit Investments",
        "COMI.CA": "Commercial International Bank (Egypt)",
        "HRHO.CA": "Hassan Allam Holding",
        "EKHO.CA": "El Kahera Housing",
        "BTFH.CA": "Beltone Financial Holding",
    }



    def __init__(self):

        self.file = pd.DataFrame()

        self.live_quotes = pd.DataFrame()

        self.african_markets = pd.DataFrame()

    # ==========================================
    # Yahoo Finance Historical Data
    # ==========================================
    def api(self, start_date, end_date):

        symbols = list(self.CompaniesNamesStock.keys())

        data = yf.download(
            tickers=symbols,
            start=start_date,
            end=end_date,
            group_by="ticker",
            threads=True,
            auto_adjust=False
        )

        allData = []

        for symbol in symbols:

            try:

                if symbol not in data:
                    continue

                df = data[symbol].copy()

                if df.empty:
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
    # Mubasher Live Quotes (BeautifulSoup)
    # ==========================================
    def mubasher_live_quotes(self):

        url = "https://www.mubasher.info/stocks"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            soup = BeautifulSoup(
                response.content,
                "html.parser"
            )

            quotes = []

            rows = soup.find_all(
                "tr",
                {"class": "quote-row"}
            )

            for row in rows:

                try:

                    tds = row.find_all("td")

                    if len(tds) >= 4:

                        quotes.append({
                            "Symbol": tds[0].text.strip(),
                            "Price": tds[1].text.strip(),
                            "Change": tds[2].text.strip(),
                            "Volume": tds[3].text.strip()
                        })

                except Exception as row_error:

                    print(f"Row Error -> {row_error}")

            if len(quotes) == 0:

                print("No Mubasher data found")
                return pd.DataFrame()

            self.live_quotes = pd.DataFrame(quotes)

            return self.live_quotes

        except requests.exceptions.RequestException as e:

            print(f"Request failed -> {e}")
            return pd.DataFrame()

        except Exception as e:

            print(f"Error -> {e}")
            return pd.DataFrame()

    # ==========================================
    # African Markets (Selenium)
    # ==========================================
    def african_markets_scraper(self):

        options = Options()

        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(
            options=options
        )

        try:

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

                if cells:

                    row_data = [
                        cell.text.strip()
                        for cell in cells
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
