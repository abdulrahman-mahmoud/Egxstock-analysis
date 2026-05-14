import os
import pandas as pd
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

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
    SHORT_WINDOW = 21
    LONG_WINDOW = 63
    VOL_WINDOW = 30

    def __init__(self, data='data'):
        self.df = None
        self.df2 = None
        self.sector_map = None
        self.company_info_map = None
        self.error_message = None
        self.data = data
        self.decision_system = self.make_decision_system()

    def make_decision_system(self):
        momentum_1m = ctrl.Antecedent(np.arange(-20, 21, 1), 'momentum_1m')
        momentum_3m = ctrl.Antecedent(np.arange(-30, 31, 1), 'momentum_3m')
        volatility = ctrl.Antecedent(np.arange(0, 81, 1), 'volatility')
        sector_strength = ctrl.Antecedent(np.arange(-10, 16, 1), 'sector_strength')
        drawdown = ctrl.Antecedent(np.arange(-60, 1, 1), 'drawdown')
        decision = ctrl.Consequent(np.arange(0, 101, 1), 'decision')

        momentum_1m['weak'] = fuzz.trimf(momentum_1m.universe, [-20, -20, 0])
        momentum_1m['steady'] = fuzz.trimf(momentum_1m.universe, [-5, 0, 5])
        momentum_1m['strong'] = fuzz.trimf(momentum_1m.universe, [0, 20, 20])

        momentum_3m['weak'] = fuzz.trimf(momentum_3m.universe, [-30, -30, 0])
        momentum_3m['steady'] = fuzz.trimf(momentum_3m.universe, [-5, 5, 12])
        momentum_3m['strong'] = fuzz.trimf(momentum_3m.universe, [5, 30, 30])

        volatility['low'] = fuzz.trimf(volatility.universe, [0, 0, 22])
        volatility['medium'] = fuzz.trimf(volatility.universe, [15, 30, 45])
        volatility['high'] = fuzz.trimf(volatility.universe, [35, 80, 80])

        sector_strength['weak'] = fuzz.trimf(sector_strength.universe, [-10, -10, 1])
        sector_strength['neutral'] = fuzz.trimf(sector_strength.universe, [-1, 2, 5])
        sector_strength['strong'] = fuzz.trimf(sector_strength.universe, [3, 15, 15])

        drawdown['severe'] = fuzz.trimf(drawdown.universe, [-60, -60, -20])
        drawdown['moderate'] = fuzz.trimf(drawdown.universe, [-30, -15, -5])
        drawdown['contained'] = fuzz.trimf(drawdown.universe, [-10, 0, 0])

        decision['risky'] = fuzz.trimf(decision.universe, [0, 0, 45])
        decision['watch'] = fuzz.trimf(decision.universe, [35, 55, 75])
        decision['attractive'] = fuzz.trimf(decision.universe, [65, 100, 100])

        rules = [
            ctrl.Rule(momentum_1m['strong'] & momentum_3m['strong'] & volatility['low'], decision['attractive']),
            ctrl.Rule(momentum_1m['strong'] & sector_strength['strong'] & drawdown['contained'], decision['attractive']),
            ctrl.Rule(momentum_3m['strong'] & volatility['medium'] & sector_strength['strong'], decision['attractive']),
            ctrl.Rule(momentum_1m['steady'] & momentum_3m['steady'] & volatility['low'], decision['watch']),
            ctrl.Rule(momentum_1m['steady'] & sector_strength['neutral'] & drawdown['moderate'], decision['watch']),
            ctrl.Rule(momentum_1m['steady'] & momentum_3m['strong'], decision['watch']),
            ctrl.Rule(momentum_1m['strong'] & volatility['medium'], decision['watch']),
            ctrl.Rule(sector_strength['neutral'] & drawdown['contained'], decision['watch']),
            ctrl.Rule(momentum_1m['weak'] | momentum_3m['weak'], decision['risky']),
            ctrl.Rule(volatility['high'] & drawdown['severe'], decision['risky']),
            ctrl.Rule(volatility['high'] & sector_strength['weak'], decision['risky']),
            ctrl.Rule(drawdown['severe'], decision['risky']),
            ctrl.Rule(volatility['low'] & sector_strength['weak'], decision['watch']),
            ctrl.Rule(drawdown['contained'] & sector_strength['strong'] & volatility['low'], decision['attractive']),
            ctrl.Rule(drawdown['moderate'] & momentum_3m['steady'], decision['watch']),
            ctrl.Rule(sector_strength['strong'], decision['watch']),
            ctrl.Rule(volatility['medium'], decision['watch']),
        ]

        return ctrl.ControlSystem(rules)

    def fallback_decision_score(
        self,
        one_month_return,
        three_month_return,
        annualized_volatility,
        sector_return_1m,
        max_drawdown
    ):
        score = 50

        if not pd.isna(one_month_return):
            score += np.clip(one_month_return * 2, -15, 15)

        if not pd.isna(three_month_return):
            score += np.clip(three_month_return, -15, 20)

        if not pd.isna(annualized_volatility):
            score -= np.clip((annualized_volatility - 20) * 0.7, 0, 20)

        if not pd.isna(sector_return_1m):
            score += np.clip(sector_return_1m * 2, -10, 10)

        if not pd.isna(max_drawdown):
            score += np.clip((max_drawdown + 20) * 0.6, -15, 10)

        return int(np.clip(round(score), 0, 100))

    def bounded_value(self, value, lower, upper, default=0):
        if pd.isna(value):
            return default
        return float(np.clip(value, lower, upper))

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

            self.company_info_map = (
                self.df2
                .drop_duplicates('Company')
                .set_index('Company')[['Sector', 'Price', 'YTD', 'M.Cap']]
                .to_dict('index')
            )
            self.df = (
                    self.df
                    .sort_values(['Company', 'Date', 'Volume'], ascending=[True, True, False])
                    .drop_duplicates(['Company', 'Date'], keep='first')
                    .reset_index(drop=True)
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

        self.df = self.df.sort_values(["Company", "Date"])

        cols = ["Open", "High", "Low", "Close", "Volume", "MarketCap"]
        for col in cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        if self.company_info_map is not None:
            cap_map = {
                company: info.get("M.Cap")
                for company, info in self.company_info_map.items()
            }

            if "MarketCap" not in self.df.columns:
                self.df["MarketCap"] = np.nan

            self.df["MarketCap"] = self.df["MarketCap"].fillna(
                self.df["Company"].map(cap_map)
            )
                
        self.df["Price_Range"] = (self.df["High"] - self.df["Low"]) / self.df["Close"]
        
        self.df["Total_Gain"] = (
            self.df.groupby("Company")["Close"]
            .transform(lambda x: (x - x.iloc[0]) / x.iloc[0] * 100)
        )

        self.df["Portfolio_Value"] = self.df.groupby("Company")["Daily_Return"].transform(
            lambda r: 10000 * (1 + r.fillna(0)).cumprod()
        )

    def company_names(self):
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

    def safe_pct_return(self, series, periods):
        series = series.dropna()

        if len(series) <= periods:
            return np.nan

        start_value = series.iloc[-(periods + 1)]
        end_value = series.iloc[-1]

        if pd.isna(start_value) or start_value == 0 or pd.isna(end_value):
            return np.nan

        return ((end_value / start_value) - 1) * 100

    def company_frame(self, company_name):
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        return (
            self.df[self.df['Company'] == company_name]
            .sort_values('Date')
            .copy()
        )

    def sector_recent_return(self, sector_name, periods=None):
        if self.df is None or self.df.empty or sector_name in [None, 'Unknown']:
            return np.nan

        periods = periods or self.SHORT_WINDOW

        sector_df = (
            self.df[self.df['Sector'] == sector_name]
            .groupby('Date')['Daily_Return']
            .mean()
            .sort_index()
            .dropna()
        )

        if len(sector_df) < periods:
            return np.nan

        return ((1 + sector_df.tail(periods)).prod() - 1) * 100

    def max_drawdown(self, close_series):
        close_series = close_series.dropna()

        if close_series.empty:
            return np.nan

        rolling_peak = close_series.cummax()
        drawdowns = ((close_series / rolling_peak) - 1) * 100
        return float(drawdowns.min())

    def company_decision(self, company_name):
        company_data = self.company_frame(company_name)

        if company_data.empty:
            return None

        company_row = self.company_info(company_name)
        close_series = company_data['Close']
        return_series = company_data['Daily_Return']

        latest_close = close_series.iloc[-1]
        volume_series = company_data['Volume'].dropna()
        latest_volume = volume_series.iloc[-1] if not volume_series.empty else np.nan
        one_month_return = self.safe_pct_return(close_series, self.SHORT_WINDOW)
        three_month_return = self.safe_pct_return(close_series, self.LONG_WINDOW)

        recent_returns = return_series.dropna().tail(self.VOL_WINDOW)
        annualized_volatility = (
            recent_returns.std() * np.sqrt(self.TRADING_DAYS) * 100
            if not recent_returns.empty else np.nan
        )

        avg_volume_30 = company_data['Volume'].dropna().tail(self.VOL_WINDOW).mean()
        universe_avg_volume = self.df.groupby('Company')['Volume'].mean().median() if self.df is not None else np.nan

        sector_name = company_row.get('Sector', 'Unknown')
        sector_return_1m = self.sector_recent_return(sector_name, self.SHORT_WINDOW)
        max_drawdown = self.max_drawdown(close_series)

        positive_days_ratio = return_series.dropna().tail(self.SHORT_WINDOW).gt(0).mean()
        short_ma = close_series.tail(self.SHORT_WINDOW).mean()
        long_ma = close_series.tail(self.LONG_WINDOW).mean() if len(close_series.dropna()) >= self.LONG_WINDOW else np.nan

        reasons = []
        red_flags = []
        if pd.isna(three_month_return):
            red_flags.append("Limited long-term price history")
        if not pd.isna(three_month_return) and three_month_return < 0:
            red_flags.append("Weak 3-month trend")
        if not pd.isna(one_month_return) and one_month_return < 0:
            red_flags.append("Recent price trend is negative")
        if not pd.isna(sector_return_1m) and sector_return_1m < 0:
            red_flags.append("Sector momentum is weak")
        if not pd.isna(annualized_volatility) and annualized_volatility > 40:
            red_flags.append("Volatility is elevated")
        if not pd.isna(max_drawdown) and max_drawdown < -20:
            red_flags.append("Drawdown has been severe")
        if not pd.isna(positive_days_ratio) and positive_days_ratio < 0.5:
            red_flags.append("Recent sessions have been inconsistent")
        if not pd.isna(avg_volume_30) and not pd.isna(universe_avg_volume) and avg_volume_30 < universe_avg_volume:
            red_flags.append("Liquidity is lighter than the market median")

        if not pd.isna(three_month_return) and three_month_return >= 8:
            reasons.append("Strong 3-month momentum")
        elif not pd.isna(three_month_return) and three_month_return > 0:
            reasons.append("Positive 3-month trend")

        if not pd.isna(one_month_return) and one_month_return >= 4:
            reasons.append("Recent momentum is strong")
        elif not pd.isna(one_month_return) and one_month_return > 0:
            reasons.append("Recent trend is positive")

        if not pd.isna(sector_return_1m) and sector_return_1m >= 2:
            reasons.append("Sector backdrop is supportive")

        if not pd.isna(annualized_volatility) and annualized_volatility <= 25:
            reasons.append("Volatility is controlled")

        if not pd.isna(positive_days_ratio) and positive_days_ratio >= 0.6:
            reasons.append("Buying pressure has been consistent")

        if not pd.isna(avg_volume_30) and not pd.isna(universe_avg_volume) and avg_volume_30 >= universe_avg_volume:
            reasons.append("Liquidity is healthy")

        if getattr(self, 'decision_system', None) is None:
            self.decision_system = self.make_decision_system()

        simulation = ctrl.ControlSystemSimulation(self.decision_system)
        simulation.input['momentum_1m'] = self.bounded_value(one_month_return, -20, 20)
        simulation.input['momentum_3m'] = self.bounded_value(three_month_return, -30, 30)
        simulation.input['volatility'] = self.bounded_value(annualized_volatility, 0, 80, default=35)
        simulation.input['sector_strength'] = self.bounded_value(sector_return_1m, -10, 15)
        simulation.input['drawdown'] = self.bounded_value(max_drawdown, -60, 0, default=-20)
        simulation.compute()

        if 'decision' in simulation.output:
            score = int(round(simulation.output['decision']))
        else:
            score = self.fallback_decision_score(
                one_month_return,
                three_month_return,
                annualized_volatility,
                sector_return_1m,
                max_drawdown
            )

        if score >= 70:
            signal = "Attractive"
        elif score >= 50:
            signal = "Watch"
        else:
            signal = "Risky"

        if not pd.isna(short_ma) and not pd.isna(long_ma):
            if short_ma > long_ma and (pd.isna(one_month_return) or one_month_return >= 0):
                timing_hint = "Trend improving"
            elif short_ma < long_ma and (pd.isna(one_month_return) or one_month_return < 0):
                timing_hint = "Trend weakening"
            else:
                timing_hint = "Trend mixed"
        else:
            timing_hint = "Trend unclear"

        if not reasons:
            reasons.append("Signal is driven by limited positive confirmations")

        return {
            "company": company_name,
            "ticker": self.get_ticker(company_name),
            "sector": sector_name,
            "decision_score": score,
            "signal": signal,
            "timing_hint": timing_hint,
            "reason": ", ".join(reasons[:3]),
            "reasons": reasons,
            "red_flags": red_flags[:4],
            "metrics": {
                "latest_close": float(latest_close) if not pd.isna(latest_close) else np.nan,
                "latest_volume": float(latest_volume) if not pd.isna(latest_volume) else np.nan,
                "one_month_return": float(one_month_return) if not pd.isna(one_month_return) else np.nan,
                "three_month_return": float(three_month_return) if not pd.isna(three_month_return) else np.nan,
                "annualized_volatility": float(annualized_volatility) if not pd.isna(annualized_volatility) else np.nan,
                "avg_volume_30": float(avg_volume_30) if not pd.isna(avg_volume_30) else np.nan,
                "sector_return_1m": float(sector_return_1m) if not pd.isna(sector_return_1m) else np.nan,
                "max_drawdown": float(max_drawdown) if not pd.isna(max_drawdown) else np.nan,
                "positive_days_ratio": float(positive_days_ratio * 100) if not pd.isna(positive_days_ratio) else np.nan,
            }
        }

    def rank_companies(self):
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        rows = []
        for company in self.company_names():
            decision = self.company_decision(company)
            if decision is None:
                continue

            rows.append({
                "Company": decision["company"],
                "Ticker": decision["ticker"],
                "Sector": decision["sector"],
                "Decision Score": decision["decision_score"],
                "Signal": decision["signal"],
                "Timing Hint": decision["timing_hint"],
                "Reason": decision["reason"],
                "Red Flags": len(decision["red_flags"]),
                "1M Return (%)": decision["metrics"]["one_month_return"],
                "3M Return (%)": decision["metrics"]["three_month_return"],
                "Volatility (%)": decision["metrics"]["annualized_volatility"],
                "Sector 1M (%)": decision["metrics"]["sector_return_1m"],
                "Max Drawdown (%)": decision["metrics"]["max_drawdown"],
                "Positive Days (%)": decision["metrics"]["positive_days_ratio"],
            })

        if not rows:
            return pd.DataFrame()

        ranked = pd.DataFrame(rows)
        return ranked.sort_values(
            by=["Decision Score", "1M Return (%)", "3M Return (%)"],
            ascending=[False, False, False]
        ).reset_index(drop=True)

    def screen_companies(
        self,
        max_volatility=None,
        min_one_month_return=None,
        min_sector_return=None,
        min_score=None
    ):
        ranked = self.rank_companies()

        if ranked.empty:
            return ranked

        if max_volatility is not None:
            ranked = ranked[
                ranked["Volatility (%)"].isna() |
                (ranked["Volatility (%)"] <= max_volatility)
            ]

        if min_one_month_return is not None:
            ranked = ranked[
                ranked["1M Return (%)"].isna() |
                (ranked["1M Return (%)"] >= min_one_month_return)
            ]

        if min_sector_return is not None:
            ranked = ranked[
                ranked["Sector 1M (%)"].isna() |
                (ranked["Sector 1M (%)"] >= min_sector_return)
            ]

        if min_score is not None:
            ranked = ranked[ranked["Decision Score"] >= min_score]

        return ranked.reset_index(drop=True)

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

    def get_ticker(self, company_name):
       df = self.df.copy()

       row = df[df["Company"] == company_name]

       if row.empty:
           return company_name

       if "Symbol" not in df.columns:
           return company_name

       symbols = row["Symbol"].dropna()

       if symbols.empty:
          return company_name

       return symbols.iloc[0]

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
    
    def get_monthly(self):
        self.df['Month'] = self.df['Date'].dt.to_period('M')
        monthly_perf = self.df.sort_values(['Company', 'Date']).groupby(['Company', 'Month'])['Close'].agg(['first', 'last'])
        monthly_perf['Monthly_Return'] = (monthly_perf['last'] / monthly_perf['first'] - 1) * 100

        return monthly_perf.reset_index()

    def get_3d_monthly_data(self):
        df = self.df.copy()

        df['Month'] = df['Date'].dt.to_period('M')

        returns = (
            df.sort_values(['Company', 'Date'])
            .groupby(['Company', 'Month'])['Close']
            .agg(['first', 'last'])
            .reset_index()
        )

        returns['Monthly_Return'] = (returns['last'] / returns['first'] - 1) * 100

        volatility = (
            df.groupby(['Company', 'Month'])['Daily_Return']
            .std()
            .reset_index(name='Monthly_Volatility')
        )

        volatility['Monthly_Volatility'] *= 100

        volume = (
            df.groupby(['Company', 'Month'])['Volume']
            .sum()
            .reset_index(name='Monthly_Volume')
        )

        merged = returns.merge(volatility, on=['Company', 'Month'], how='left')
        merged = merged.merge(volume, on=['Company', 'Month'], how='left')
        merged['Month'] = merged['Month'].astype(str)

        return merged[['Month', 'Company', 'Monthly_Return', 'Monthly_Volatility', 'Monthly_Volume']]

    def top_n_per_month(self,monthly_perf, n=5):
        results = []
        for month in sorted(monthly_perf['Month'].unique()):
            month_data = monthly_perf[monthly_perf['Month'] == month]
            gainers = month_data.nlargest(n, 'Monthly_Return')[['Company', 'Monthly_Return']].assign(Type='Gainer', Month=month)
            losers  = month_data.nsmallest(n, 'Monthly_Return')[['Company', 'Monthly_Return']].assign(Type='Loser',  Month=month)
            results.extend([gainers, losers])
        return pd.concat(results, ignore_index=True)
