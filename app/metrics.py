import numpy as np
import pandas as pd

from app.constants import TRADING_DAYS
from core.helpers import safe_annualized_volatility, safe_max_drawdown, safe_pct_return


def annualized_volatility(return_series, trading_days=TRADING_DAYS, window=None):
    return safe_annualized_volatility(return_series, trading_days, window=window)


def pct_return(series, periods):
    return safe_pct_return(series, periods)


def max_drawdown(close_series):
    return safe_max_drawdown(close_series)


def enrich_market_data(df, company_info_map=None):
    if df is None or df.empty:
        return pd.DataFrame()

    enriched = df.copy()
    enriched = enriched.sort_values(["Company", "Date"]).reset_index(drop=True)

    if "MarketCap" not in enriched.columns:
        enriched["MarketCap"] = np.nan

    if company_info_map:
        cap_map = {
            company: info.get("M.Cap")
            for company, info in company_info_map.items()
        }
        enriched["MarketCap"] = enriched["MarketCap"].fillna(
            enriched["Company"].map(cap_map)
        )

    enriched["Daily_Return"] = enriched.groupby("Company")["Close"].pct_change()
    enriched["Price_Range"] = (enriched["High"] - enriched["Low"]) / enriched["Close"]
    enriched["Total_Gain"] = (
        enriched.groupby("Company")["Close"]
        .transform(lambda x: ((x - x.iloc[0]) / x.iloc[0]) * 100 if len(x.dropna()) else np.nan)
    )
    enriched["Portfolio_Value"] = enriched.groupby("Company")["Daily_Return"].transform(
        lambda r: 10000 * (1 + r.fillna(0)).cumprod()
    )

    return enriched


def monthly_performance(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Company", "Month", "first", "last", "Monthly_Return"])

    monthly_perf = (
        df.sort_values(["Company", "Date"])
        .assign(Month=lambda x: x["Date"].dt.to_period("M").astype(str))
        .groupby(["Company", "Month"])["Close"]
        .agg(["first", "last"])
    )
    monthly_perf["Monthly_Return"] = (monthly_perf["last"] / monthly_perf["first"] - 1) * 100
    return monthly_perf.reset_index()


def company_monthly_returns(df, company_name):
    company_df = df[df["Company"] == company_name].copy()
    if company_df.empty:
        return pd.DataFrame(columns=["Month", "Monthly_Return"])

    monthly = (
        company_df.sort_values("Date")
        .assign(Month=lambda x: x["Date"].dt.to_period("M").astype(str))
        .groupby("Month")["Close"]
        .agg(["first", "last"])
    )
    monthly["Monthly_Return"] = (monthly["last"] / monthly["first"] - 1) * 100
    return monthly.reset_index()[["Month", "Monthly_Return"]]


def rolling_volatility(df, company_name, window=30):
    company_df = df[df["Company"] == company_name].copy()
    if company_df.empty:
        return pd.DataFrame(columns=["date", "volatility"])

    company_df["volatility"] = (
        company_df["Daily_Return"]
        .rolling(window=window)
        .std() * np.sqrt(TRADING_DAYS) * 100
    )

    return (
        company_df[["Date", "volatility"]]
        .dropna()
        .rename(columns={"Date": "date"})
        .reset_index(drop=True)
    )


def three_d_monthly_data(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Month", "Company", "Monthly_Return", "Monthly_Volatility", "Monthly_Volume"])

    data = df.copy()
    data["Month"] = data["Date"].dt.to_period("M")

    returns = (
        data.sort_values(["Company", "Date"])
        .groupby(["Company", "Month"])["Close"]
        .agg(["first", "last"])
        .reset_index()
    )
    returns["Monthly_Return"] = (returns["last"] / returns["first"] - 1) * 100

    volatility = (
        data.groupby(["Company", "Month"])["Daily_Return"]
        .std()
        .reset_index(name="Monthly_Volatility")
    )
    volatility["Monthly_Volatility"] *= 100

    volume = (
        data.groupby(["Company", "Month"])["Volume"]
        .sum(min_count=1)
        .reset_index(name="Monthly_Volume")
    )

    merged = returns.merge(volatility, on=["Company", "Month"], how="left")
    merged = merged.merge(volume, on=["Company", "Month"], how="left")
    merged["Month"] = merged["Month"].astype(str)
    return merged[["Month", "Company", "Monthly_Return", "Monthly_Volatility", "Monthly_Volume"]]


def top_n_per_month(monthly_perf, n=5):
    if monthly_perf is None or monthly_perf.empty:
        return pd.DataFrame(columns=["Company", "Monthly_Return", "Type", "Month"])

    results = []
    for month in sorted(monthly_perf["Month"].unique()):
        month_data = monthly_perf[monthly_perf["Month"] == month]
        gainers = month_data.nlargest(n, "Monthly_Return")[["Company", "Monthly_Return"]].assign(Type="Gainer", Month=month)
        losers = month_data.nsmallest(n, "Monthly_Return")[["Company", "Monthly_Return"]].assign(Type="Loser", Month=month)
        results.extend([gainers, losers])

    if not results:
        return pd.DataFrame(columns=["Company", "Monthly_Return", "Type", "Month"])

    return pd.concat(results, ignore_index=True)
