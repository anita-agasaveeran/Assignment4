"""Loading and basic typing of the raw bakery dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DATA_RAW, FRESH_MAX_SHELF_LIFE_DAYS

EXPECTED_COLUMNS = [
    "Order_ID", "Customer_ID", "Customer_Age", "Customer_Gender", "Customer_Segment",
    "Loyalty_Member", "Date", "Year", "Month", "Day", "Day_of_Week", "Weekend", "Hour",
    "Time", "Season", "Festival", "Weather", "Temperature", "Product", "Category",
    "Quantity", "Unit_Price", "Cost_Price", "Discount_Percentage", "Selling_Price",
    "Total_Bill", "Payment_Method", "Promotion_Applied", "Promotion_Type",
    "Shelf_Life_Days", "Storage_Type", "Perishability", "Store_ID", "Units_Produced",
    "Units_Sold", "Unsold_Units", "Stock_Available", "Waste_Pct", "Profit",
    "Customer_Rating",
]
YES_NO_COLUMNS = ["Loyalty_Member", "Weekend", "Promotion_Applied"]


def load_raw(path: str | Path = DATA_RAW, typed: bool = True) -> pd.DataFrame:
    """Read the raw CSV and check its schema.

    With ``typed=True`` the function parses ``Date``, turns the Yes/No
    columns into booleans and fills a blank ``Festival`` /
    ``Promotion_Type`` with ``"None"``, since blank means "no festival /
    no promotion" here and isn't really missing. Nothing else changes.
    Cleaning happens in Data Preparation.
    """
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    extra = set(df.columns) - set(EXPECTED_COLUMNS)
    if missing or extra:
        raise ValueError(f"Schema mismatch. Missing: {sorted(missing)}; unexpected: {sorted(extra)}")
    if not typed:
        return df

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    for col in YES_NO_COLUMNS:
        bad = set(df[col].unique()) - {"Yes", "No"}
        if bad:
            raise ValueError(f"{col} has values other than Yes/No: {bad}")
        df[col] = df[col].eq("Yes")
    df["Festival"] = df["Festival"].fillna("None")
    df["Promotion_Type"] = df["Promotion_Type"].fillna("None")
    return df


def fresh_products(df: pd.DataFrame, max_days: int = FRESH_MAX_SHELF_LIFE_DAYS) -> list[str]:
    """Products whose median ``Shelf_Life_Days`` is at most ``max_days``.

    The median is used because shelf life varies between rows of the
    same product (e.g. Juice ranges from 1 day to more).
    """
    median = df.groupby("Product")["Shelf_Life_Days"].median()
    return sorted(median[median <= max_days].index)
