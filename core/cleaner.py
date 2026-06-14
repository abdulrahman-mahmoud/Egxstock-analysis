import numpy as np
import pandas as pd

from core.constants import FALLBACK_METADATA, NAME_MAP, SECTORS
from core.helpers import safe_map


def normalize_company_names(df, column="Company"):
    if df is None or df.empty or column not in df.columns:
        return df

    cleaned = df.copy()
    cleaned[column] = cleaned[column].replace(NAME_MAP)
    return cleaned


def _clean_history_frame(df):
    cleaned = df.copy()
    cleaned.columns = cleaned.columns.str.strip()
    cleaned = cleaned.drop(["Capital Gains", "Dividends", "Stock Splits"], axis=1, errors="ignore")

    numeric_cols = ["Open", "High", "Low", "Close", "Volume", "MarketCap"]
    for col in numeric_cols:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    if "Date" in cleaned.columns:
        cleaned["Date"] = pd.to_datetime(cleaned["Date"], utc=True, errors="coerce").dt.tz_convert(None)

    required_cols = [col for col in ["Company", "Date"] if col in cleaned.columns]
    if not required_cols:
        return cleaned.iloc[0:0].copy()

    cleaned = cleaned.dropna(subset=required_cols).reset_index(drop=True)
    cleaned = normalize_company_names(cleaned)

    if "Volume" in cleaned.columns:
        volume_has_activity = cleaned.groupby("Company")["Volume"].transform(
            lambda s: s.fillna(0).gt(0).any()
        )
        cleaned.loc[~volume_has_activity, "Volume"] = np.nan

    sort_cols = ["Company", "Date"]
    sort_order = [True, True]
    if "Volume" in cleaned.columns:
        sort_cols.append("Volume")
        sort_order.append(False)

    cleaned = (
        cleaned
        .sort_values(sort_cols, ascending=sort_order)
        .drop_duplicates(["Company", "Date"], keep="first")
        .reset_index(drop=True)
    )

    return cleaned


def _clean_sector_frame(df):
    cleaned = df.copy()
    cleaned.columns = cleaned.columns.str.strip()
    cleaned = normalize_company_names(cleaned)

    if "Sector" not in cleaned.columns:
        cleaned["Sector"] = np.nan

    cleaned = cleaned[cleaned["Sector"].isin(SECTORS)].copy()
    required_cols = [col for col in ["Company", "Sector"] if col in cleaned.columns]
    if not required_cols:
        return cleaned.iloc[0:0].copy()

    cleaned = cleaned.dropna(subset=required_cols).reset_index(drop=True)

    for col in ["Price", "M.Cap", "1D", "YTD"]:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(
                cleaned[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace("+", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip(),
                errors="coerce",
            )

    return cleaned


def build_company_info_map(stock_df):
    if stock_df is None or stock_df.empty:
        return {}

    if "Company" not in stock_df.columns or "Sector" not in stock_df.columns:
        return {}

    prepared = stock_df.copy()
    for col in ["Price", "YTD", "M.Cap"]:
        if col not in prepared.columns:
            prepared[col] = np.nan

    company_info_map = (
        prepared
        .drop_duplicates("Company")
        .set_index("Company")[["Sector", "Price", "YTD", "M.Cap"]]
        .to_dict("index")
    )

    for company, info in FALLBACK_METADATA.items():
        company_info_map.setdefault(company, info.copy())

    return company_info_map


def build_sector_map(company_info_map):
    return {
        company: info.get("Sector")
        for company, info in (company_info_map or {}).items()
        if info.get("Sector")
    }


def clean_datasets(raw_df, stock_df):
    cleaned_raw = _clean_history_frame(raw_df)
    cleaned_stock = _clean_sector_frame(stock_df)
    company_info_map = build_company_info_map(cleaned_stock)
    sector_map = build_sector_map(company_info_map)

    cleaned_raw["Sector"] = safe_map(cleaned_raw["Company"], sector_map, default="Unknown")

    return cleaned_raw, cleaned_stock, company_info_map, sector_map
