import os
import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from core.metrics import (
    annualized_volatility,
    enrich_market_data,
    max_drawdown,
    monthly_performance,
    pct_return,
    rolling_volatility,
    three_d_monthly_data,
)
from core.sector import sector_growth_data, sector_recent_return
from core.loader import load_data_files
from core.cleaner import clean_datasets
from core.constants import LONG_WINDOW, SHORT_WINDOW, TRADING_DAYS, VOL_WINDOW


class EgxAnalyzer:

    def __init__(self, data="data"):
        self.df = None
        self.df2 = None
        self.sector_map = None
        self.company_info_map = None
        self.error_message = None
        self.data = data
        self.decision_system = self.make_decision_system()

    def make_decision_system(self):
        if ctrl is None or fuzz is None:
            return None

        momentum_1m = ctrl.Antecedent(np.arange(-20, 21, 1), "momentum_1m")
        momentum_3m = ctrl.Antecedent(np.arange(-30, 31, 1), "momentum_3m")
        volatility = ctrl.Antecedent(np.arange(0, 81, 1), "volatility")
        sector_strength = ctrl.Antecedent(np.arange(-10, 16, 1), "sector_strength")
        drawdown = ctrl.Antecedent(np.arange(-60, 1, 1), "drawdown")
        decision = ctrl.Consequent(np.arange(0, 101, 1), "decision")

        momentum_1m["weak"] = fuzz.trimf(momentum_1m.universe, [-20, -20, 0])
        momentum_1m["steady"] = fuzz.trimf(momentum_1m.universe, [-5, 0, 5])
        momentum_1m["strong"] = fuzz.trimf(momentum_1m.universe, [0, 20, 20])

        momentum_3m["weak"] = fuzz.trimf(momentum_3m.universe, [-30, -30, 0])
        momentum_3m["steady"] = fuzz.trimf(momentum_3m.universe, [-5, 5, 12])
        momentum_3m["strong"] = fuzz.trimf(momentum_3m.universe, [5, 30, 30])

        volatility["low"] = fuzz.trimf(volatility.universe, [0, 0, 22])
        volatility["medium"] = fuzz.trimf(volatility.universe, [15, 30, 45])
        volatility["high"] = fuzz.trimf(volatility.universe, [35, 80, 80])

        sector_strength["weak"] = fuzz.trimf(sector_strength.universe, [-10, -10, 1])
        sector_strength["neutral"] = fuzz.trimf(sector_strength.universe, [-1, 2, 5])
        sector_strength["strong"] = fuzz.trimf(sector_strength.universe, [3, 15, 15])

        drawdown["severe"] = fuzz.trimf(drawdown.universe, [-60, -60, -20])
        drawdown["moderate"] = fuzz.trimf(drawdown.universe, [-30, -15, -5])
        drawdown["contained"] = fuzz.trimf(drawdown.universe, [-10, 0, 0])

        decision["risky"] = fuzz.trimf(decision.universe, [0, 0, 45])
        decision["watch"] = fuzz.trimf(decision.universe, [35, 55, 75])
        decision["attractive"] = fuzz.trimf(decision.universe, [65, 100, 100])

        rules = [
            ctrl.Rule(momentum_1m["strong"] & momentum_3m["strong"] & volatility["low"], decision["attractive"]),
            ctrl.Rule(momentum_1m["strong"] & sector_strength["strong"] & drawdown["contained"], decision["attractive"]),
            ctrl.Rule(momentum_3m["strong"] & volatility["medium"] & sector_strength["strong"], decision["attractive"]),
            ctrl.Rule(momentum_1m["steady"] & momentum_3m["steady"] & volatility["low"], decision["watch"]),
            ctrl.Rule(momentum_1m["steady"] & sector_strength["neutral"] & drawdown["moderate"], decision["watch"]),
            ctrl.Rule(momentum_1m["steady"] & momentum_3m["strong"], decision["watch"]),
            ctrl.Rule(momentum_1m["strong"] & volatility["medium"], decision["watch"]),
            ctrl.Rule(sector_strength["neutral"] & drawdown["contained"], decision["watch"]),
            ctrl.Rule(momentum_1m["weak"] | momentum_3m["weak"], decision["risky"]),
            ctrl.Rule(volatility["high"] & drawdown["severe"], decision["risky"]),
            ctrl.Rule(volatility["high"] & sector_strength["weak"], decision["risky"]),
            ctrl.Rule(drawdown["severe"], decision["risky"]),
            ctrl.Rule(volatility["low"] & sector_strength["weak"], decision["watch"]),
            ctrl.Rule(drawdown["contained"] & sector_strength["strong"] & volatility["low"], decision["attractive"]),
            ctrl.Rule(drawdown["moderate"] & momentum_3m["steady"], decision["watch"]),
            ctrl.Rule(sector_strength["strong"], decision["watch"]),
            ctrl.Rule(volatility["medium"], decision["watch"]),
        ]

        return ctrl.ControlSystem(rules)

    def fallback_decision_score(self, one_month_return, three_month_return, annualized_volatility_value, sector_return_1m, max_drawdown_value):
        score = 50

        if not pd.isna(one_month_return):
            score += np.clip(one_month_return * 2, -15, 15)

        if not pd.isna(three_month_return):
            score += np.clip(three_month_return, -15, 20)

        if not pd.isna(annualized_volatility_value):
            score -= np.clip((annualized_volatility_value - 20) * 0.7, 0, 20)

        if not pd.isna(sector_return_1m):
            score += np.clip(sector_return_1m * 2, -10, 10)

        if not pd.isna(max_drawdown_value):
            score += np.clip((max_drawdown_value + 20) * 0.6, -15, 10)

        return int(np.clip(round(score), 0, 100))

    def bounded_value(self, value, lower, upper, default=0):
        if pd.isna(value):
            return default
        return float(np.clip(value, lower, upper))

    def latest_valid_volume(self, company_data):
        if "Volume" not in company_data.columns:
            return np.nan

        volume_series = company_data["Volume"].replace(0, np.nan).dropna()
        if volume_series.empty:
            return np.nan

        return float(volume_series.iloc[-1])

    # REMINDER: SQL REPLACEMENT POINT
    def load_data(self):
        # REMINDER: SQL REPLACEMENT POINT
        try:
            self.df, self.df2 = load_data_files(self.data)
            return True
        except Exception as e:
            self.error_message = f"Error loading data: {e}"
            return False

    def clean(self):
        try:
            self.df, self.df2, self.company_info_map, self.sector_map = clean_datasets(self.df, self.df2)
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

        self.df = enrich_market_data(self.df, self.company_info_map)

    def company_names(self):
        if self.df is None or self.df.empty:
            return []
        return sorted(self.df["Company"].dropna().unique().tolist())

    def company_frame(self, company_name):
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        return self.df[self.df["Company"] == company_name].sort_values("Date").copy()

    def specific_company(self, company_name):
        company_data = self.company_frame(company_name)
        company_row = self.company_info(company_name)

        if len(company_data) == 0:
            return None

        latest = company_data.iloc[-1]
        annl_vol = annualized_volatility(company_data["Daily_Return"])

        company_summary = company_data[
            ["Open", "High", "Low", "Close", "Volume", "Daily_Return"]
        ].dropna().describe().to_dict()

        return {
            "company name": company_name,
            "sector": company_row.get("Sector", "Unknown"),
            "ytd": company_row.get("YTD", np.nan),
            "fundamental_price": company_row.get("Price", np.nan),
            "market_cap_fundamental": company_row.get("M.Cap", np.nan),
            "date_min": company_data["Date"].min(),
            "date_max": company_data["Date"].max(),
            "latest": {
                "date": latest["Date"],
                "close": float(latest["Close"]),
                "volume": self.latest_valid_volume(company_data),
                "market_cap": float(latest["MarketCap"]),
            },
            "performance": {
                "daily_return_avg": float(company_data["Daily_Return"].mean() * 100),
                "total_gain": float(latest["Total_Gain"]),
                "portfolio_value": float(latest["Portfolio_Value"]),
            },
            "risk": {
                "annualized_volatility": float(annl_vol),
                "price_range_avg": float(company_data["Price_Range"].mean() * 100),
            },
            "summary_stats": company_summary,
        }

    def sector_recent_return(self, sector_name, periods=None):
        return sector_recent_return(self.df, sector_name, periods or SHORT_WINDOW)

    def company_decision(self, company_name):
        company_data = self.company_frame(company_name)

        if company_data.empty:
            return None

        company_row = self.company_info(company_name)
        close_series = company_data["Close"]
        return_series = company_data["Daily_Return"]

        latest_close = close_series.iloc[-1]
        latest_volume = self.latest_valid_volume(company_data)
        volume_data_available = not pd.isna(latest_volume)
        one_month_return = pct_return(close_series, SHORT_WINDOW)
        three_month_return = pct_return(close_series, LONG_WINDOW)

        recent_returns = return_series.dropna().tail(VOL_WINDOW)
        annualized_volatility_value = (
            recent_returns.std() * np.sqrt(TRADING_DAYS) * 100
            if not recent_returns.empty else np.nan
        )

        avg_volume_30 = company_data["Volume"].replace(0, np.nan).dropna().tail(VOL_WINDOW).mean()
        universe_avg_volume = (
            self.df.groupby("Company")["Volume"].mean().dropna().median()
            if self.df is not None else np.nan
        )

        sector_name = company_row.get("Sector", "Unknown")
        sector_return_1m = self.sector_recent_return(sector_name, SHORT_WINDOW)
        max_drawdown_value = max_drawdown(close_series)

        positive_days_ratio = return_series.dropna().tail(SHORT_WINDOW).gt(0).mean()
        short_ma = close_series.tail(SHORT_WINDOW).mean()
        long_ma = close_series.tail(LONG_WINDOW).mean() if len(close_series.dropna()) >= LONG_WINDOW else np.nan

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
        if not pd.isna(annualized_volatility_value) and annualized_volatility_value > 40:
            red_flags.append("Volatility is elevated")
        if not pd.isna(max_drawdown_value) and max_drawdown_value < -20:
            red_flags.append("Drawdown has been severe")
        if not pd.isna(positive_days_ratio) and positive_days_ratio < 0.5:
            red_flags.append("Recent sessions have been inconsistent")
        if volume_data_available and not pd.isna(avg_volume_30) and not pd.isna(universe_avg_volume) and avg_volume_30 < universe_avg_volume:
            red_flags.append("Liquidity is lighter than the market median")
        if not volume_data_available:
            red_flags.append("Volume data is unavailable")

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

        if not pd.isna(annualized_volatility_value) and annualized_volatility_value <= 25:
            reasons.append("Volatility is controlled")

        if not pd.isna(positive_days_ratio) and positive_days_ratio >= 0.6:
            reasons.append("Buying pressure has been consistent")

        if volume_data_available and not pd.isna(avg_volume_30) and not pd.isna(universe_avg_volume) and avg_volume_30 >= universe_avg_volume:
            reasons.append("Liquidity is healthy")

        if getattr(self, "decision_system", None) is None:
            self.decision_system = self.make_decision_system()

        if self.decision_system is not None and ctrl is not None:
            simulation = ctrl.ControlSystemSimulation(self.decision_system)
            simulation.input["momentum_1m"] = self.bounded_value(one_month_return, -20, 20)
            simulation.input["momentum_3m"] = self.bounded_value(three_month_return, -30, 30)
            simulation.input["volatility"] = self.bounded_value(annualized_volatility_value, 0, 80, default=35)
            simulation.input["sector_strength"] = self.bounded_value(sector_return_1m, -10, 15)
            simulation.input["drawdown"] = self.bounded_value(max_drawdown_value, -60, 0, default=-20)
            simulation.compute()

            if "decision" in simulation.output:
                score = int(round(simulation.output["decision"]))
            else:
                score = self.fallback_decision_score(
                    one_month_return,
                    three_month_return,
                    annualized_volatility_value,
                    sector_return_1m,
                    max_drawdown_value,
                )
        else:
            score = self.fallback_decision_score(
                one_month_return,
                three_month_return,
                annualized_volatility_value,
                sector_return_1m,
                max_drawdown_value,
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
                "latest_volume": latest_volume,
                "one_month_return": float(one_month_return) if not pd.isna(one_month_return) else np.nan,
                "three_month_return": float(three_month_return) if not pd.isna(three_month_return) else np.nan,
                "annualized_volatility": float(annualized_volatility_value) if not pd.isna(annualized_volatility_value) else np.nan,
                "avg_volume_30": float(avg_volume_30) if not pd.isna(avg_volume_30) else np.nan,
                "sector_return_1m": float(sector_return_1m) if not pd.isna(sector_return_1m) else np.nan,
                "max_drawdown": float(max_drawdown_value) if not pd.isna(max_drawdown_value) else np.nan,
                "positive_days_ratio": float(positive_days_ratio * 100) if not pd.isna(positive_days_ratio) else np.nan,
            },
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
            ascending=[False, False, False],
        ).reset_index(drop=True)

    def screen_companies(self, max_volatility=None, min_one_month_return=None, min_sector_return=None, min_score=None):
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
        if self.df is None or self.df.empty:
            return []

        risk = self.df.groupby("Company")["Daily_Return"].agg(
            Mean_Daily_Return="mean",
            Std_Daily_Return="std",
        ).dropna()
        risk["Ann_Return"] = risk["Mean_Daily_Return"] * TRADING_DAYS
        risk["Ann_Volatility"] = risk["Std_Daily_Return"] * np.sqrt(TRADING_DAYS)
        risk = risk.reset_index()
        risk["Sector"] = risk["Company"].map(self.sector_map or {}).fillna("Unknown")
        return risk.sort_values("Ann_Volatility", ascending=False).to_dict("records")

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
        return sector_growth_data(self.df)

    def get_rolling_volatility_data(self, company_name, window=30):
        data = rolling_volatility(self.df, company_name, window=window)
        return data.to_dict("records")

    def get_monthly(self):
        return monthly_performance(self.df)

    def get_3d_monthly_data(self):
        return three_d_monthly_data(self.df)

    def top_activity_companies(self, n=15):
        if self.df is None or self.df.empty:
            return []
        return self.df["Company"].value_counts().head(n).index.tolist()
