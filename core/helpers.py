import numpy as np
import pandas as pd


def safe_map(series, mapping, default=np.nan):
    mapped = pd.Series(series).map(mapping)
    if pd.isna(default):
        return mapped
    return mapped.fillna(default)


def safe_groupby(df, keys, value_col=None, agg="mean"):
    if df is None or df.empty:
        return pd.DataFrame()

    grouped = df.groupby(keys)
    if value_col is None:
        return grouped

    if isinstance(agg, str):
        return grouped[value_col].agg(agg)

    return grouped[value_col].agg(agg)


def safe_pct_return(series, periods):
    series = pd.Series(series).dropna()

    if len(series) <= periods:
        return np.nan

    start_value = series.iloc[-(periods + 1)]
    end_value = series.iloc[-1]

    if pd.isna(start_value) or start_value == 0 or pd.isna(end_value):
        return np.nan

    return float(((end_value / start_value) - 1) * 100)


def safe_max_drawdown(close_series):
    close_series = pd.Series(close_series).dropna()

    if close_series.empty:
        return np.nan

    rolling_peak = close_series.cummax()
    drawdowns = ((close_series / rolling_peak) - 1) * 100
    return float(drawdowns.min())


def safe_annualized_volatility(return_series, trading_days, window=None):
    series = pd.Series(return_series).dropna()

    if window is not None:
        series = series.tail(window)

    if series.empty:
        return np.nan

    return float(series.std() * np.sqrt(trading_days) * 100)
