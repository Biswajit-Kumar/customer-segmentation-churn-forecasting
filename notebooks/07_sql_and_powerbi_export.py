# %% [markdown]
# # 07 · SQL Version of RFM + Power BI Data Export
#
# **Part A:** load the clean data into a **SQL database** (SQLite) and rebuild RFM in pure SQL (`sql/rfm_analysis.sql`).
# **Part B:** export a clean **star schema** of CSV files for the Power BI dashboard.
#
# > 📘 **Why SQL too?** In a bank, data lives in databases/warehouses (HSBC mentions BigQuery and SQL in the JD). Analysts pull and shape data with SQL *before* Python or Power BI. Showing the same logic in both proves you can work at either layer.
# >
# > **SQLite** is a full SQL database stored in a single file, with no server to install. The SQL here (CTEs, window functions like `NTILE`, `LAG`, `SUM() OVER()`) is standard and transfers to PostgreSQL, SQL Server or BigQuery.

# %%
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
PROCESSED = ROOT / "data" / "processed"
PBI = ROOT / "powerbi" / "data"
PBI.mkdir(parents=True, exist_ok=True)
pd.set_option("display.float_format", "{:,.2f}".format)

sales = pd.read_parquet(PROCESSED / "sales_clean.parquet")

# %% [markdown]
# ## Part A: SQL
# ### 1. Load clean sales into a SQLite database

# %%
db_path = ROOT / "data" / "retail.db"
con = sqlite3.connect(db_path)
cols = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price", "Revenue", "CustomerID", "Country"]
sql_sales = sales[cols].copy()
sql_sales["InvoiceDate"] = sql_sales["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S")
sql_sales.to_sql("sales", con, if_exists="replace", index=False)
con.execute("CREATE INDEX IF NOT EXISTS idx_customer ON sales(CustomerID)")
print(pd.read_sql("SELECT COUNT(*) AS rows, COUNT(DISTINCT CustomerID) AS customers FROM sales", con))

# %% [markdown]
# ### 2. Run the queries from `sql/rfm_analysis.sql`

# %%
queries = [q.strip() for q in (ROOT / "sql" / "rfm_analysis.sql").read_text(encoding="utf-8").split(";") if "SELECT" in q]
print(f"{len(queries)} queries found")

rfm_sql = pd.read_sql(queries[0], con)
rfm_sql.to_sql("rfm_sql", con, if_exists="replace", index=False)
rfm_sql.head()

# %% [markdown]
# **Query 2: segment summary**

# %%
pd.read_sql(queries[1], con)

# %% [markdown]
# **Query 3: monthly revenue & month-over-month growth (LAG window function)**

# %%
pd.read_sql(queries[2], con).tail(8)

# %% [markdown]
# **Query 4: repeat-purchase rate by country**

# %%
pd.read_sql(queries[3], con).head(10)

# %% [markdown]
# ### 3. Reconcile SQL vs Python
# **Reconciliation** (checking two systems give the same answer) is a daily task in Finance Operations. R, F, M raw values should match exactly. Segments may differ slightly because `NTILE` and `pd.qcut` break **ties** differently (e.g. many customers share Frequency = 1).

# %%
rfm_py = pd.read_parquet(PROCESSED / "rfm_clusters.parquet")
cmp = rfm_py.merge(rfm_sql, on="CustomerID")
print(f"Customers matched: {len(cmp):,} / {len(rfm_py):,}")
print(f"Recency identical:   {(cmp['Recency'] == cmp['recency']).mean():.1%}")
print(f"Frequency identical: {(cmp['Frequency'] == cmp['frequency']).mean():.1%}")
print(f"Monetary identical:  {np.isclose(cmp['Monetary'], cmp['monetary'], atol=0.01).mean():.1%}")
print(f"Segment agreement:   {(cmp['Segment'] == cmp['segment']).mean():.1%}  (differences = tie-breaking at quintile edges)")
con.close()

# %% [markdown]
# 🔎 **A real reconciliation catch:** the first SQL version computed recency as `DATE(snapshot) − DATE(last purchase)` (calendar days), while Python counted *full 24-hour days elapsed*. Result: **0% of recency values matched**, every customer off by one day. Aligning the definition (subtract the full timestamp, truncate the fraction) fixed it. Lesson: when two systems disagree, the cause is usually a **definition** difference, not an arithmetic bug. Document definitions explicitly.

# %% [markdown]
# ## Part B: Power BI export (star schema)
# > 📘 **Star schema:** one central **fact table** (transactions, many rows) linked to **dimension tables** (customers, products, dates: descriptive attributes). It's the recommended model shape for Power BI: faster, simpler DAX, fewer errors.
# >
# > ```
# >            DimDate (built in DAX)
# >                 │
# > DimProduct ── FactSales ── DimCustomer ── SegmentActions
# > ```
# > Plus standalone tables for cohort retention and the forecast.

# %%
# Power BI compares text case-INsensitively and ignores trailing spaces, but pandas doesn't: codes like
# "15056bl" vs "15056BL" (170 of them) and "47503J " vs "47503J" are the same product and would be duplicate
# keys in DimProduct → trim and upper-case them for the BI layer.
sales = sales.assign(StockCode=sales["StockCode"].str.strip().str.upper())

fact = sales[["Invoice", "InvoiceDate", "Date", "StockCode", "CustomerID", "Country", "Quantity", "Price", "Revenue"]].copy()
fact["CustomerID"] = fact["CustomerID"].astype("Int64")
fact.to_csv(PBI / "FactSales.csv", index=False)

product = (sales.groupby("StockCode")
           .agg(Description=("Description", lambda d: d.mode().iat[0] if d.notna().any() else "Unknown"),
                AvgPrice=("Price", "median"))
           .reset_index())
product.to_csv(PBI / "DimProduct.csv", index=False)

scores = pd.read_parquet(PROCESSED / "customer_scores.parquet")
cust = rfm_py.merge(scores[["CustomerID", "ChurnProbability", "RiskBand", "QuarterlyRevenue", "RevenueAtRisk"]],
                    on="CustomerID", how="left")
cust["RiskBand"] = cust["RiskBand"].astype("string").fillna("Inactive (>1 yr)")
cust = cust.drop(columns=["Cluster"])
cust.to_csv(PBI / "DimCustomer.csv", index=False)

seg = pd.read_csv(PROCESSED / "segment_actions.csv").drop(columns=["Customers", "% Revenue"])
seg["SortOrder"] = range(1, len(seg) + 1)  # best → worst, used for "Sort by column" in Power BI
seg.to_csv(PBI / "SegmentActions.csv", index=False)
pd.read_csv(PROCESSED / "cohort_retention.csv").to_csv(PBI / "CohortRetention.csv", index=False)
pd.read_csv(PROCESSED / "weekly_forecast.csv").to_csv(PBI / "WeeklyForecast.csv", index=False)

for f in sorted(PBI.glob("*.csv")):
    print(f"{f.name:22s} {len(pd.read_csv(f, usecols=[0])):>9,} rows  {f.stat().st_size/1e6:6.1f} MB")

# Key checks: dimension keys must be unique (case-insensitively, as Power BI sees them)
for name, df, keycol in [("DimProduct", product, "StockCode"), ("DimCustomer", cust, "CustomerID"), ("SegmentActions", seg, "Segment")]:
    dups = df[keycol].astype(str).str.strip().str.upper().duplicated().sum()
    print(f"{name}[{keycol}] duplicate keys: {dups}")
    assert dups == 0

# %% [markdown]
# ## ✅ Key takeaways
# 1. The same RFM logic works in **SQL** with CTEs + window functions; raw R/F/M reconcile exactly with Python.
# 2. Small segment differences come from **tie-breaking**, a real-world reconciliation issue worth explaining.
# 3. Data is exported as a **star schema** for Power BI. See `powerbi/POWERBI_BUILD_GUIDE.md` for the dashboard steps.
