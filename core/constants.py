import numpy as np


SECTORS = [
    "Financials",
    "Basic Materials",
    "Industrials",
    "Consumer Goods",
    "Consumer Services",
    "Technology",
    "Health Care",
    "Utilities",
    "Telecom",
    "Oil & Gas",
]


NAME_MAP = {
    "Abu Kir Fertilizers": "Abu Qir Fertilizers",
    "Alexandria Container & Cargo Handling": "Alexandria Containers And Goods",
    "Alexandria Mineral Oils": "Alexandria Mineral Oils Company",
    "Cairo Poultry (Koki)": "Cairo Poultry",
    "Commercial International Bank (CIB)": "Commercial International Bank (Egypt)",
    "CIB Egypt": "Commercial International Bank (Egypt)",
    "Egyptian Electrical Cables": "Electro Cable Egypt Company",
    "El Sewedy Electric": "El Sewedy Electric Company",
    "Fawry": "Fawry for Banking Technology and Electronic Payment",
    "Misr Capital": "Misr Financial Investments",
    "Orascom Construction": "Orascom Construction Industries",
    "Orascom Telecom Media & Technology": "Global Telecom Holding",
    "Palm Hills Developments": "Palm Hills Development Company",
    "Raya Holding": "Raya Holding for Financial Investments",
    "Talaat Moustafa Group": "TMG Holding",
}


FALLBACK_METADATA = {
    "Unit Investments": {
        "Sector": "Financials",
        "Price": np.nan,
        "YTD": np.nan,
        "M.Cap": np.nan,
    },
    "Hassan Allam Holding": {
        "Sector": "Industrials",
        "Price": np.nan,
        "YTD": np.nan,
        "M.Cap": np.nan,
    },
    "Modern Furniture": {
        "Sector": "Consumer Goods",
        "Price": np.nan,
        "YTD": np.nan,
        "M.Cap": np.nan,
    },
}


TRADING_DAYS = 252
SHORT_WINDOW = 21
LONG_WINDOW = 63
VOL_WINDOW = 30
