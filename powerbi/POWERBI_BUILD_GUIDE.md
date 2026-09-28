# Power BI Dashboard: Step-by-Step Build Guide (Dark Premium design)

**Time needed:** ~2–2.5 hours the first time. **No sign-in needed.** Close the sign-in popup; everything works offline.

**How the design works:** each page has a ready-made **background image** (`powerbi/backgrounds/`) with the sidebar, header, KPI tiles and panel titles already drawn. You place **transparent visuals** inside the panels at the exact positions listed below. The dark theme (`theme.json`) makes every visual's text light and its background transparent automatically.

| Page | Background | Question it answers |
|---|---|---|
| Overview | `01_overview.png` | How is the business doing? |
| Segments | `02_segments.png` | Who are our customers and who matters most? |
| Churn Risk | `03_churn.png` | Who is likely to leave and how much is at stake? |
| Cohorts | `04_cohorts.png` | Do new customers come back? |
| Forecast | `05_forecast.png` | What revenue should we expect next quarter? |

> 📏 **Positions:** every visual has *X, Y, W, H* values. Select a visual → **Format** pane → **General** → **Properties** → type them into **Position** (Horizontal = X, Vertical = Y) and **Size** (Width = W, Height = H). They are in the same 1280 × 720 units as the page.

---

## Part 1: Load the data (≈10 min)

1. **Home → Get data → Text/CSV** → `powerbi/data/FactSales.csv`.
2. In the preview window, click the **small arrow ⌄ next to Load → Transform Data**.
3. Click the `1²3` icon on the **Invoice** column → **Text** → *Replace current*. (IDs should be text, never numbers you'd add up.)
4. **Home → New Source → Text/CSV** for each of: `DimCustomer.csv`, `DimProduct.csv`, `SegmentActions.csv`, `CohortRetention.csv`, `WeeklyForecast.csv` → **OK**.
5. Check the types (icon left of each column name):

| Table | Column | Type |
|---|---|---|
| FactSales | Date | **Date** (not Date/Time) |
| FactSales | StockCode, Country | Text |
| DimCustomer | ChurnProbability, RevenueAtRisk, QuarterlyRevenue, Monetary | Decimal number |
| DimCustomer | R, F, M, Frequency | Whole number |
| DimProduct | StockCode | Text |
| CohortRetention | Cohort | Text |
| WeeklyForecast | WeekEnding | Date |

6. **Home → Close & Apply** (≈1 min for 1M rows).

> 📘 **Power Query vs DAX:** Power Query shapes data *before* loading; DAX calculates *after* loading. Clean upstream, calculate downstream.

---

## Part 2: Model setup (≈10 min)

### 2.1 Date table

**Modeling → New table**:

```DAX
DimDate =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2009, 12, 1 ), DATE ( 2012, 3, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "MonthNum", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "YearMonth", FORMAT ( [Date], "YYYY-MM" ),
    "Weekday", FORMAT ( [Date], "ddd" ),
    "WeekdayNum", WEEKDAY ( [Date], 2 )
)
```

- **Table tools → Mark as date table** → column `Date`.
- Select `Month` → **Column tools → Sort by column → MonthNum**. Select `Weekday` → Sort by `WeekdayNum`.

### 2.2 Relationships (Model view, 3rd icon on the left)

Drag to connect, all **Many-to-one**, single direction:

| From (many) | To (one) |
|---|---|
| FactSales[Date] | DimDate[Date] |
| FactSales[CustomerID] | DimCustomer[CustomerID] |
| FactSales[StockCode] | DimProduct[StockCode] |
| DimCustomer[Segment] | SegmentActions[Segment] |

`CohortRetention` and `WeeklyForecast` stay unconnected.

> 📘 This is a **star schema**: one fact table in the centre, dimension tables around it.

### 2.3 Sorting

- `SegmentActions[Segment]` → Sort by column → `SortOrder`.

### 2.4 Theme

**View → Themes → Browse for themes** → `powerbi/theme.json`.

---

## Part 3: DAX measures (≈15 min)

**Home → Enter data** → name the table `_Measures` → **Load**. Select it → **New measure** for each:

```DAX
-- Overview
Total Revenue = SUM ( FactSales[Revenue] )
Total Orders = DISTINCTCOUNT ( FactSales[Invoice] )
Active Customers = DISTINCTCOUNTNOBLANK ( FactSales[CustomerID] )
Avg Order Value = DIVIDE ( [Total Revenue], [Total Orders] )
Revenue PY = CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
Revenue YoY % = DIVIDE ( [Total Revenue] - [Revenue PY], [Revenue PY] )

-- Segments
Customers = COUNTROWS ( DimCustomer )
% of Customers = DIVIDE ( [Customers], CALCULATE ( [Customers], ALL ( DimCustomer ) ) )
Customer Revenue = SUM ( DimCustomer[Monetary] )
% of Revenue = DIVIDE ( [Customer Revenue], CALCULATE ( [Customer Revenue], ALL ( DimCustomer ) ) )
Repeat Customer Rate = DIVIDE ( CALCULATE ( [Customers], DimCustomer[Frequency] > 1 ), [Customers] )
Champions Revenue % = CALCULATE ( [% of Revenue], DimCustomer[Segment] = "Champions" )
Lapsing Revenue = CALCULATE ( [Customer Revenue], DimCustomer[Segment] IN { "At Risk", "Can't Lose Them" } )

-- Churn
Revenue at Risk = SUM ( DimCustomer[RevenueAtRisk] )
High Risk Customers = CALCULATE ( [Customers], DimCustomer[RiskBand] = "High" )
Avg Churn Probability = AVERAGE ( DimCustomer[ChurnProbability] )

-- Cohorts (weighted by cohort size; Dec-2009 excluded because it holds pre-existing customers)
Retention % = DIVIDE ( SUM ( CohortRetention[ActiveCustomers] ), SUM ( CohortRetention[CohortSize] ) )
New Cohort Retention = CALCULATE ( [Retention %], CohortRetention[Cohort] <> "2009-12" )
Month-1 Retention = CALCULATE ( [New Cohort Retention], CohortRetention[MonthIndex] = 1 )
Month-3 Retention = CALCULATE ( [New Cohort Retention], CohortRetention[MonthIndex] = 3 )
Month-12 Retention = CALCULATE ( [New Cohort Retention], CohortRetention[MonthIndex] = 12 )
One-Time Buyers % = DIVIDE ( CALCULATE ( [Customers], DimCustomer[Frequency] = 1 ), [Customers] )

-- Forecast
Forecast Next Quarter = SUM ( WeeklyForecast[Forecast] )
Forecast Low (80%) = SUM ( WeeklyForecast[Lower80] )
Forecast High (80%) = SUM ( WeeklyForecast[Upper80] )
```

(Create each line as a separate measure. The `--` lines are just labels, so don't paste those.)

**Formatting** (select measure → Measure tools): £ measures → Currency, **£ English (United Kingdom)**, 0 decimals, and **Display units: Millions or Thousands** where the card is small. `%` measures → Percentage, 1 decimal.

> 📘 **Key DAX ideas:** `CALCULATE` changes the filter context · `ALL()` removes filters (→ % of total) · `DIVIDE()` avoids divide-by-zero errors.

---

## Part 4: Build page 1 (Overview), your template (≈40 min)

### 4.1 Page setup

1. Rename "Page 1" → **Overview** (double-click the tab).
2. **Format pane (paintbrush with page selected) → Canvas settings:** Type **16:9** (1280 × 720).
3. **Canvas background →** Browse → `backgrounds/01_overview.png` → **Image fit: Fit** → **Transparency: 0%**.
4. **Wallpaper →** colour `#070D1A` (the area around the canvas).

### 4.2 KPI cards (5 cards)

Insert → **Card** visual (the classic card). For each, drag the measure into *Fields* and set position:

| Measure | X | Y | W | H |
|---|---|---|---|---|
| Total Revenue | 198 | 118 | 185 | 56 |
| Total Orders | 415 | 118 | 185 | 56 |
| Active Customers | 632 | 118 | 185 | 56 |
| Avg Order Value | 850 | 118 | 185 | 56 |
| Revenue YoY % | 1067 | 118 | 185 | 56 |

If the card still shows a label under the number or a white background: *Format → Visual → Category label: Off*, *General → Effects → Background: Off*. Callout value: white, ~24pt, left-aligned. (If your version only has the **new Card**, apply the same: turn off label, background and border.)

Build **one** card perfectly, then **Ctrl+C / Ctrl+V** it and just swap the measure. Much faster.

### 4.3 Charts

| Panel | Visual | Fields | X | Y | W | H |
|---|---|---|---|---|---|---|
| Monthly revenue | **Area chart** | X: DimDate[YearMonth] · Y: Total Revenue, Revenue PY | 198 | 234 | 644 | 213 |
| Top 10 markets | **Bar chart** | Y: FactSales[Country] · X: Total Revenue | 878 | 234 | 374 | 213 |
| Orders by weekday | **Column chart** | X: DimDate[Weekday] · Y: Total Orders | 198 | 504 | 414 | 188 |

- **Top 10 markets:** Filters pane → Country → *Basic filtering* → Select all, then **untick United Kingdom**. Then *Filter type: Top N* → Top 10 by Total Revenue. Turn on **Data labels**.
- **Area chart:** colours: Total Revenue teal, Revenue PY grey (`#526179`). Legend at top-right.
- The *Key Insights* panel is already in the background, so nothing to add there.

### 4.4 Slicers (top right)

| Slicer | Field | Style | X | Y | W | H |
|---|---|---|---|---|---|---|
| Year | DimDate[Year] | Dropdown | 935 | 26 | 155 | 38 |
| Country | FactSales[Country] | Dropdown | 1105 | 26 | 155 | 38 |

(Format → Slicer settings → Style: **Dropdown**.)

### 4.5 Sidebar navigation buttons

Insert → **Buttons → Blank**. Set: *Action: On* → **Type: Page navigation** → Destination: the page. Turn **Fill** off and **Border** off (the background already draws the menu). Optional: *Style → State: On hover → Fill: white, transparency 90%* for a subtle hover glow.

| Button → page | X | Y | W | H |
|---|---|---|---|---|
| Overview | 12 | 124 | 146 | 36 |
| Segments | 12 | 170 | 146 | 36 |
| Churn Risk | 12 | 216 | 146 | 36 |
| Cohorts | 12 | 262 | 146 | 36 |
| Forecast | 12 | 308 | 146 | 36 |

> Page navigation only works once those pages exist. Create them in 4.6 first, then come back and set destinations. In Desktop, **Ctrl + click** a button to test it.

### 4.6 Create the other 4 pages fast

Right-click the **Overview** tab → **Duplicate page** (4 times). Rename to *Segments, Churn Risk, Cohorts, Forecast*. On each: change the **canvas background** image, delete the old charts/cards you don't need, and keep the **nav buttons** (already positioned). Then build each page below.

---

## Part 5: Remaining pages

### Segments (`02_segments.png`)

| Panel | Visual | Fields | X | Y | W | H |
|---|---|---|---|---|---|---|
| KPI Customers | Card | Customers | 198 | 118 | 240 | 56 |
| KPI Repeat rate | Card | Repeat Customer Rate | 470 | 118 | 240 | 56 |
| KPI Champions share | Card | Champions Revenue % | 741 | 118 | 240 | 56 |
| KPI Revenue at risk | Card | Lapsing Revenue | 1012 | 118 | 240 | 56 |
| % customers vs % revenue | **Clustered bar** | Y: SegmentActions[Segment] · X: % of Customers, % of Revenue | 198 | 234 | 594 | 213 |
| Revenue by segment | **Treemap** | Category: DimCustomer[Segment] · Values: Customer Revenue | 828 | 234 | 424 | 213 |
| R × F grid | **Matrix** | Rows: DimCustomer[F] · Columns: DimCustomer[R] · Values: Customers | 198 | 504 | 354 | 188 |
| Segment playbook | **Table** | SegmentActions[Segment], [Priority], [Recommended action] | 588 | 504 | 664 | 188 |
| Slicer | Slicer (dropdown) | DimCustomer[ClusterName] | 1105 | 26 | 155 | 38 |

- **Clustered bar:** colours: % of Customers grey `#526179`, % of Revenue teal. Data labels on. This is the money chart: Champions' teal bar towers over the grey one.
- **R×F matrix heatmap:** sort rows F descending (click the "…" → Sort). *Format → Cell elements → Background color: On → fx → Gradient* from `#0E172A` (lowest) to `#2DD4BF` (highest). Font colour white.
- **Playbook table:** column headers and values are already themed; turn **Text wrap** on for the action column.

### Churn Risk (`03_churn.png`)

| Panel | Visual | Fields | X | Y | W | H |
|---|---|---|---|---|---|---|
| KPI | Card | Revenue at Risk | 198 | 118 | 240 | 56 |
| KPI | Card | High Risk Customers | 470 | 118 | 240 | 56 |
| KPI | Card | Avg Churn Probability | 741 | 118 | 240 | 56 |
| (ROC-AUC 0.77 is already in the background) | | | | | | |
| Value vs risk | **Scatter chart** | Values: DimCustomer[CustomerID] · X: QuarterlyRevenue · Y: ChurnProbability · Legend: RiskBand | 198 | 234 | 594 | 213 |
| Risk bands | **Donut chart** | Legend: DimCustomer[RiskBand] · Values: Customers | 828 | 234 | 424 | 213 |
| Priority call list | **Table** | CustomerID, Segment, Country, ChurnProbability, QuarterlyRevenue, RevenueAtRisk | 198 | 504 | 644 | 188 |
| At risk by segment | **Bar chart** | Y: DimCustomer[Segment] · X: Revenue at Risk | 878 | 504 | 374 | 188 |
| Slicer | Slicer (dropdown) | DimCustomer[Segment] | 1105 | 26 | 155 | 38 |

- **Scatter:** set X and Y fields to *Don't summarize* (click the ⌄ on the field). X-axis → **Scale type: Log**. Colour by RiskBand: High = rose `#FB7185`, Medium = amber `#F59E0B`, Low = teal `#2DD4BF`. Top-right = valuable **and** risky.
- **Donut & scatter:** add a visual filter *RiskBand is not "Inactive (>1 yr)"*.
- **Call list:** sort by RevenueAtRisk descending → Filters → CustomerID → *Top N* 20 by **Revenue at Risk**. Add conditional formatting *Data bars* on RevenueAtRisk (rose). Set CustomerID to "Don't summarize".

### Cohorts (`04_cohorts.png`)

| Panel | Visual | Fields | X | Y | W | H |
|---|---|---|---|---|---|---|
| KPI | Card | Month-1 Retention | 198 | 118 | 240 | 56 |
| KPI | Card | Month-3 Retention | 470 | 118 | 240 | 56 |
| KPI | Card | Month-12 Retention | 741 | 118 | 240 | 56 |
| KPI | Card | One-Time Buyers % | 1012 | 118 | 240 | 56 |
| Heatmap | **Matrix** | Rows: CohortRetention[Cohort] · Columns: CohortRetention[MonthIndex] · Values: Retention % | 198 | 234 | 674 | 458 |
| Retention curve | **Line chart** | X: CohortRetention[MonthIndex] · Y: New Cohort Retention | 908 | 234 | 344 | 213 |

- **Heatmap:** visual filter *MonthIndex ≤ 12*. *Cell elements → Background color → Gradient* `#0E172A` → `#2DD4BF`, with **Maximum = 0.5** (a custom value, so the 100% month-0 column doesn't wash everything out). Values font size 8; turn off row/column subtotals.
- **Line chart:** X-axis type **Categorical**, markers on, teal line; visual filter *MonthIndex ≤ 12*.

### Forecast (`05_forecast.png`)

| Panel | Visual | Fields | X | Y | W | H |
|---|---|---|---|---|---|---|
| KPI | Card | Forecast Next Quarter | 198 | 118 | 185 | 56 |
| KPI | Card | Forecast Low (80%) | 415 | 118 | 185 | 56 |
| KPI | Card | Forecast High (80%) | 632 | 118 | 185 | 56 |
| (WAPE 12.1% and bias −0.9% are in the background) | | | | | | |
| Main chart | **Line chart** | X: WeeklyForecast[WeekEnding] · Y: Actual, Backtest_Ensemble, Forecast, Lower80, Upper80 | 198 | 234 | 1054 | 263 |

- Line styles (*Format → Lines → apply settings to series*): Actual = `#E2E8F0` solid 2px · Backtest_Ensemble = violet **dashed** · Forecast = amber solid 3px · Lower80/Upper80 = grey `#526179` **dotted** 1px.
- X-axis: *Type: Continuous*. Legend: top.
- The leaderboard and "How it works" panels are in the background already.

---

## Part 6: Final polish checklist

- [ ] Every page: no white visual backgrounds or borders left (select each → General → Effects → Background **Off**).
- [ ] No leftover visual titles overlapping the panel titles (Title **Off**; the background already has them).
- [ ] Hover over charts: tooltips appear dark (theme handles this).
- [ ] **View → Sync slicers** → let the Year/Country slicers apply to all pages if you want.
- [ ] Test navigation buttons with **Ctrl + click**.
- [ ] Reconcile numbers with the checklist below.

## Part 7: Save & share

1. **File → Save as** → `powerbi/Customer_Analytics_Dashboard.pbix`.
2. **File → Export → Export to PDF** → save in `reports/`.
3. **Screenshot each page** (Win + Shift + S) → save in `reports/dashboard/` (e.g. `overview.png`), used on GitHub and LinkedIn.

> Publishing to the Power BI web service needs a work/school account, so it's not required. The .pbix + PDF + screenshots are what recruiters look at.

## Number checklist (reconciliation)

| Metric | Expected |
|---|---|
| Total Revenue | £19,327,627 |
| Total Orders | 39,510 |
| Customers | 5,852 |
| Repeat Customer Rate | 72.3% |
| Champions Revenue % | 52.7% |
| Lapsing Revenue | £1,470,566 |
| Revenue at Risk | £441,666 |
| High Risk Customers | 2,077 |
| Avg Churn Probability | 53.4% |
| Month-1 / 3 / 12 Retention | 20.7% / 20.8% / 18.0% |
| One-Time Buyers % | 27.7% |
| Forecast Next Quarter | £1.91M (80%: £1.35M – £2.54M) |

## If you change a background

Edit text/layout in `powerbi/make_backgrounds.py` (e.g. insight wording) and run `python powerbi/make_backgrounds.py`. Then in Power BI re-select the image in *Canvas background*.
