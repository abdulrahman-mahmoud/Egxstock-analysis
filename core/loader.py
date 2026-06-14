import os

import pandas as pd


def load_data_files(data_dir):
    raw_path = os.path.join(data_dir, "raw.csv")
    stock_path = os.path.join(data_dir, "stock_data.csv")

    # REMINDER: SQL REPLACEMENT POINT
    # REMINDER: SQL LAYER (future migration point)
    # Future migration can replace these file reads with database queries.
    if not os.path.isfile(raw_path):
        raise FileNotFoundError(f"File not found: {raw_path}")

    if not os.path.isfile(stock_path):
        raise FileNotFoundError(f"File not found: {stock_path}")

    return pd.read_csv(raw_path), pd.read_csv(stock_path)
