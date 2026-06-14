import numpy as np
import pandas as pd

from core.constants import SHORT_WINDOW


def sector_recent_return(df, sector_name, periods=SHORT_WINDOW):
    if df is None or df.empty or sector_name in [None, "Unknown"]:
        return np.nan

    sector_df = (
        df[df["Sector"] == sector_name]
        .groupby("Date")["Daily_Return"]
        .mean()
        .sort_index()
        .dropna()
    )

    if len(sector_df) < periods:
        return np.nan

    return float(((1 + sector_df.tail(periods)).prod() - 1) * 100)


def sector_growth_data(df, initial=10000):
    if df is None or df.empty:
        return {}

    sector_daily = df.groupby(["Date", "Sector"])["Daily_Return"].mean().reset_index()
    sector_daily = sector_daily.sort_values("Date")

    results = {}
    for sector in sector_daily["Sector"].dropna().unique():
        sdata = sector_daily[sector_daily["Sector"] == sector].copy()
        sdata["Daily_Return"] = sdata["Daily_Return"].fillna(0)
        sdata["Portfolio_Value"] = initial * (1 + sdata["Daily_Return"]).cumprod()
        results[sector] = sdata[["Date", "Portfolio_Value"]].to_dict("records")

    return results
