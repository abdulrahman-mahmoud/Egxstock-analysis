import os
import pandas as pd
import numpy as np

class EgxAnalyzer:

    SECTORS = [
    'Financials', 'Basic Materials', 'Industrials', 'Consumer Goods',
    'Consumer Services', 'Technology', 'Health Care', 'Utilities', 'Telecom', 'Oil & Gas']

    NAME_MAP = {
    'Abu Kir Fertilizers':                   'Abu Qir Fertilizers',
    'Alexandria Container & Cargo Handling': 'Alexandria Containers And Goods',
    'Alexandria Mineral Oils':               'Alexandria Mineral Oils Company',
    'Cairo Poultry (Koki)':                  'Cairo Poultry',
    'Commercial International Bank (CIB)':   'Commercial International Bank (Egypt)',
    'CIB Egypt':   'Commercial International Bank (Egypt)',
    'Egyptian Electrical Cables':            'Electro Cable Egypt Company',
    'El Sewedy Electric':                    'El Sewedy Electric Company',
    'Fawry':                                 'Fawry for Banking Technology and Electronic Payment',
    'Misr Capital':                          'Misr Financial Investments',
    'Orascom Construction':                  'Orascom Construction Industries',
    'Orascom Telecom Media & Technology':    'Global Telecom Holding',
    'Palm Hills Developments':               'Palm Hills Development Company',
    'Raya Holding':                          'Raya Holding for Financial Investments',
    'Talaat Moustafa Group':                 'TMG Holding',
    }

    FALLBACK_METADATA = {
    'Unit Investments': {
        'Sector': 'Financials',
        'Price': np.nan,
        'YTD': np.nan,
        'M.Cap': np.nan,
    },
    'Hassan Allam Holding': {
        'Sector': 'Industrials',
        'Price': np.nan,
        'YTD': np.nan,
        'M.Cap': np.nan,
    },
    'Modern Furniture': {
        'Sector': 'Consumer Goods',
        'Price': np.nan,
        'YTD': np.nan,
        'M.Cap': np.nan,
    },
    }

    TRADING_DAYS = 252

    def __init__(self, data='data'):
        self.df = None
        self.df2 = None
        self.sector_map = None
        self.company_info_map = None
        self.error_message = None
        self.data = data

    def load_data(self):
        try:
            path1 = os.path.join(self.data, 'raw.csv')
            path2 = os.path.join(self.data , 'stock_data.csv')

            if not os.path.isfile(path1):
                self.error_message = f"File not found: {path1}"
                return False

            if not os.path.isfile(path2):
                self.error_message = f"File not found: {path2}"
                return False

            self.df = pd.read_csv(path1)
            self.df2 = pd.read_csv(path2)

            return True

        except Exception as e:
            self.error_message = f"Error loading data: {e}"
            return False

    def clean(self):
        try:
            self.df.columns = self.df.columns.str.strip()
            self.df = self.df.drop(['Capital Gains', 'Dividends', 'Stock Splits'], axis=1, errors='ignore')

            for col in ['Open', 'High', 'Low', 'Close', 'Volume', 'MarketCap']:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

            self.df['Date'] = pd.to_datetime(self.df['Date'], utc=True, errors='coerce').dt.tz_convert(None)
            self.df = self.df.dropna(subset=['Company', 'Date']).reset_index(drop=True)

            self.df2 = self.df2[self.df2['Sector'].isin(self.SECTORS)].copy()
            self.df2 = self.df2.dropna(subset=['Company', 'Sector']).reset_index(drop=True)

            for col in ['Price', 'M.Cap', '1D', 'YTD']:
                self.df2[col] = pd.to_numeric(
                    self.df2[col].astype(str)
                    .str.replace('%','',regex=False)
                    .str.replace('+','',regex=False)
                    .str.replace(',','',regex=False)
                    .str.strip(),
                    errors='coerce'
                )

            self.df['Company'] = self.df['Company'].replace(self.NAME_MAP)
            self.df2['Company'] = self.df2['Company'].replace(self.NAME_MAP)

            self.df = self.df.sort_values(['Company', 'Date']).drop_duplicates(['Company', 'Date'], keep='last')

            self.company_info_map = (
                self.df2
                .drop_duplicates('Company')
                .set_index('Company')[['Sector', 'Price', 'YTD', 'M.Cap']]
                .to_dict('index')
            )

            for company, info in self.FALLBACK_METADATA.items():
                if company not in self.company_info_map:
                    self.company_info_map[company] = info.copy()

            self.sector_map = (
                pd.Series({
                    company: info.get('Sector')
                    for company, info in self.company_info_map.items()
                })
                .dropna()
                .to_dict()
            )

            self.df['Sector'] = self.df['Company'].map(self.sector_map)
            self.df['Sector'] = self.df['Sector'].fillna('Unknown')
            self.df['Daily_Return'] = self.df.groupby('Company')['Close'].pct_change()

            return True

        except Exception as e:
            self.error_message = f"Error loading data: {e}"
            return False

    def company_info(self, company_name):
        if self.company_info_map is None:
            return {}

        return self.company_info_map.get(company_name, {})
    

    def checker(self):
        if self.df is None or self.df.empty:
            return

        # 1. Numeric Conversion

        cols = ["Open", "High", "Low", "Close", "Volume", "MarketCap"]
        for col in cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        # 2. MarketCap Fill

        if self.company_info_map is not None:
            cap_map = {
                company: info.get("M.Cap")
                for company, info in self.company_info_map.items()
            }
            self.df["MarketCap"] = self.df["MarketCap"].fillna(self.df["Company"].map(cap_map))

        
        self.df["Price_Range"] = (self.df["High"] - self.df["Low"]) / self.df["Close"]
        
        self.df["Total_Gain"] = (
            self.df.groupby("Company")["Close"]
            .transform(lambda x: (x - x.iloc[0]) / x.iloc[0] * 100)
        )

        self.df["Portfolio_Value"] = (
            10000 * (1 + self.df["Daily_Return"].fillna(0))
            .groupby(self.df["Company"])
            .cumprod()
        )



    def company_names(self):
        self.df['Company'] = self.df['Company'].replace(self.NAME_MAP)
        return sorted(self.df['Company'].dropna().unique().tolist())

    def specific_company(self, company_name):

        company_data = self.df[self.df['Company'] == company_name]
        company_row = self.company_info(company_name)

        if len(company_data) == 0:
            return None

        company_data = company_data.sort_values('Date')
        latest = company_data.iloc[-1]

        annl_vol = (
            company_data['Daily_Return']
            .dropna()
            .std()
            * np.sqrt(self.TRADING_DAYS)
            * 100
        )

        company_summary = company_data[
            ['Open', 'High', 'Low', 'Close', 'Volume', 'Daily_Return']
        ].dropna().describe().to_dict()

        return {
            "company name": company_name,
            "sector": company_row.get('Sector', 'Unknown'),
            "ytd": company_row.get('YTD', np.nan),
            "fundamental_price": company_row.get('Price', np.nan),
            "market_cap_fundamental": company_row.get('M.Cap', np.nan),

            'date_min': company_data['Date'].min(),
            'date_max': company_data['Date'].max(),

            'latest': {
                'date': latest['Date'],
                'close': float(latest['Close']),
                'volume': float(latest['Volume']),
                'market_cap': float(latest['MarketCap'])
            },

            'performance': {
                'daily_return_avg': float(company_data['Daily_Return'].mean() * 100),
                'total_gain': float(latest['Total_Gain']),
                'portfolio_value': float(latest['Portfolio_Value'])
            },

            'risk': {
                'annualized_volatility': float(annl_vol),
                'price_range_avg': float(company_data['Price_Range'].mean() * 100)
            },

            'summary_stats': company_summary
        }

    def get_volatility_data(self):

        risk = self.df.groupby('Company')['Daily_Return'].agg(
            Mean_Daily_Return='mean',
            Std_Daily_Return='std'
        ).dropna()

        risk['Ann_Return'] = risk['Mean_Daily_Return'] * self.TRADING_DAYS
        risk['Ann_Volatility'] = risk['Std_Daily_Return'] * np.sqrt(self.TRADING_DAYS)

        risk = risk.reset_index()

        if self.sector_map is None:
            self.sector_map = {}

        risk['Sector'] = risk['Company'].map(self.sector_map).fillna('Unknown')

        return risk.sort_values('Ann_Volatility', ascending=False).to_dict('records')

    def get_sector_growth_data(self):

        if self.df is None or 'Sector' not in self.df.columns:
            return {}

        sector_daily = self.df.groupby(['Date', 'Sector'])['Daily_Return'].mean().reset_index()
        sector_daily = sector_daily.sort_values('Date')

        results = {}
        initial = 10000

        for sector in sector_daily['Sector'].dropna().unique():

            sdata = sector_daily[sector_daily['Sector'] == sector].copy()
            sdata['Daily_Return'] = sdata['Daily_Return'].fillna(0)

            sdata['Portfolio_Value'] = initial * (1 + sdata['Daily_Return']).cumprod()

            results[sector] = sdata[['Date', 'Portfolio_Value']].to_dict('records')

        return results
    
    def get_rolling_volatility_data(self, company_name, window=30):
        company_data = self.df[self.df['Company'] == company_name].copy()
        company_data['volatility'] = (
            company_data['Daily_Return']
            .rolling(window=window)
            .std() * np.sqrt(self.TRADING_DAYS) * 100
        )
        return company_data[['Date', 'volatility']].dropna().rename(columns={'Date': 'date'}).to_dict('records')

    def unmatched_companies(self):
        if self.df is None or self.df.empty:
            return []

        matched = set(self.sector_map.keys()) if self.sector_map is not None else set()

        return sorted(
            self.df.loc[~self.df['Company'].isin(matched), 'Company']
            .dropna()
            .unique()
            .tolist()
        )

    def duplicate_company_names(self):
        if self.df is None or self.df.empty:
            return []

        if 'Symbol' in self.df.columns:
            counts = self.df.groupby('Company')['Symbol'].nunique()
            return counts[counts > 1].index.tolist()

        counts = self.df2['Company'].value_counts() if self.df2 is not None else pd.Series(dtype=int)

        return counts[counts > 1].index.tolist()
    
