# Data: Bakery Sales Dataset

| Item | Value |
|---|---|
| File | `raw/bakery_sales_dataset.csv` (UTF-8 with BOM, 19,321 rows × 40 columns) |
| Source | Kaggle: [*Bakery Sales, Customer & Inventory Analytics Dataset*](https://www.kaggle.com/datasets/sdcloud/historical-bakery-sales-dataset) by **sdcloud** (last updated 2026-10-15) |
| Licence | CC0: Public Domain |
| Nature | **Synthetic.** The publisher describes it as a synthetic two-year bakery retail dataset for educational and ML research use |
| SHA-256 | `7538db8eac4b314f7a59909bbc3fe8cd8541b982f2bc5c96133c7a27a42c32dd` |
| Grain | One row per **order line** (an order = one `Order_ID`, 1–7 products) |
| Coverage | 2023-01-01 → 2024-12-31 · 3 stores · 500 customers · 35 products · 7 categories |

`raw/` is never modified. Everything derived from it is written to `processed/` by the notebook or `src/bakery`.

## Columns

Counts are distinct values in the raw file. The meanings are working definitions and are checked in the *Verify Data Quality* task.

| Column | Type | Distinct | Example | Meaning |
|---|---|---|---|---|
| `Order_ID` | str | 6,576 | ORD00001 | Order (basket) identifier |
| `Customer_ID` | str | 500 | CUST0328 | Customer identifier |
| `Customer_Age` | int | 57 | 46 | Age in years |
| `Customer_Gender` | str | 3 | Other | Gender |
| `Customer_Segment` | str | 4 | Young Professional | Marketing segment |
| `Loyalty_Member` | str | 2 | Yes | Loyalty-programme member |
| `Date` | str | 731 | 2023-01-01 | Order date |
| `Year`, `Month`, `Day` | int | 2 / 12 / 31 | 2023 / 1 / 1 | Calendar parts of `Date` |
| `Day_of_Week` | str | 7 | Sunday | Weekday name |
| `Weekend` | str | 2 | Yes | Saturday/Sunday flag |
| `Hour`, `Time` | int / str | 15 / 872 | 8 / 8:47 | Order time |
| `Season` | str | 4 | Winter | Season |
| `Festival` | str | 9 (+ blank) | New Year | Festival on that date; blank = none |
| `Weather` | str | 6 | Foggy | Weather condition |
| `Temperature` | float | 305 | 21.2 | Temperature (°C) |
| `Product` | str | 35 | Pastry | Product name |
| `Category` | str | 7 | Pastry & Sweet | Product category |
| `Quantity` | int | 17 | 6 | Units ordered on this line |
| `Unit_Price` | float | 7,711 | 62.49 | List price per unit (₹) |
| `Cost_Price` | float | 6,232 | 29.72 | Cost per unit (₹) |
| `Discount_Percentage` | float | 292 | 14.7 | Discount applied (%) |
| `Selling_Price` | float | 8,657 | 53.3 | Price per unit after discount (₹) |
| `Total_Bill` | float | 11,349 | 319.8 | Line total (₹) |
| `Payment_Method` | str | 4 | Cash | Payment method |
| `Promotion_Applied` | str | 2 | Yes | Promotion flag |
| `Promotion_Type` | str | 5 (+ blank) | Festival | Promotion type; blank = none |
| `Shelf_Life_Days` | int | 498 | 3 | Shelf life (days) |
| `Storage_Type` | str | 3 | Refrigerated | Storage requirement |
| `Perishability` | str | 4 | Very High | Perishability level |
| `Store_ID` | str | 3 | ST02 | Store |
| `Units_Produced` | int | 45 | 8 | Units baked for this line |
| `Units_Sold` | int | 30 | 6 | Units sold |
| `Unsold_Units` | int | 16 | 2 | Units produced but not sold (`Units_Produced − Units_Sold`, which holds on every row) |
| `Stock_Available` | int | 17 | 2 | Stock remaining |
| `Waste_Pct` | float | 100 | 25.0 | Unsold ÷ produced × 100 |
| `Profit` | float | 8,460 | 141.48 | Line profit (₹) |
| `Customer_Rating` | int | 5 | 4 | Rating 1–5 |
