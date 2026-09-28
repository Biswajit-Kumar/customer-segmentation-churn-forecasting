-- =====================================================================
-- RFM analysis in SQL (SQLite dialect, runs almost unchanged on
-- PostgreSQL / BigQuery / SQL Server with minor date-function tweaks)
-- Table: sales(Invoice, StockCode, Quantity, InvoiceDate, Price, Revenue, CustomerID, Country)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Query 1: RFM scores and segments per customer
-- Concepts: CTEs (WITH), aggregation, window functions (NTILE), CASE
-- ---------------------------------------------------------------------
WITH snapshot AS (                          -- "today" = day after the last transaction
    SELECT DATE(MAX(InvoiceDate), '+1 day') AS snap_date FROM sales
),
customer_rfm AS (                           -- raw R, F, M per customer
    SELECT
        s.CustomerID,
        -- full days elapsed (fraction truncated), same definition as the Python version
        CAST(JULIANDAY(sn.snap_date) - JULIANDAY(MAX(s.InvoiceDate)) AS INTEGER) AS recency,
        COUNT(DISTINCT s.Invoice)  AS frequency,
        ROUND(SUM(s.Revenue), 2)   AS monetary
    FROM sales s CROSS JOIN snapshot sn
    WHERE s.CustomerID IS NOT NULL
    GROUP BY s.CustomerID
),
scored AS (                                 -- 1-5 scores with NTILE (quintiles)
    SELECT *,
        NTILE(5) OVER (ORDER BY recency DESC)  AS r_score,   -- most recent → 5
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)  AS m_score
    FROM customer_rfm
)
SELECT
    CustomerID, recency, frequency, monetary, r_score, f_score, m_score,
    CASE
        WHEN r_score = 5 AND f_score >= 4             THEN 'Champions'
        WHEN r_score IN (3, 4) AND f_score >= 4       THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score IN (2, 3)       THEN 'Potential Loyalists'
        WHEN r_score = 5 AND f_score = 1              THEN 'New Customers'
        WHEN r_score = 4 AND f_score = 1              THEN 'Promising'
        WHEN r_score = 3 AND f_score = 3              THEN 'Need Attention'
        WHEN r_score = 3 AND f_score <= 2             THEN 'About to Sleep'
        WHEN r_score <= 2 AND f_score = 5             THEN 'Can''t Lose Them'
        WHEN r_score <= 2 AND f_score IN (3, 4)       THEN 'At Risk'
        ELSE 'Hibernating'
    END AS segment
FROM scored
ORDER BY monetary DESC;

-- ---------------------------------------------------------------------
-- Query 2: Segment summary with share of revenue
-- Concepts: aggregate over a subquery, window SUM() OVER () for % of total
-- ---------------------------------------------------------------------
-- (run against the rfm_sql table created from Query 1)
SELECT
    segment,
    COUNT(*)                                              AS customers,
    ROUND(AVG(recency), 1)                                AS avg_recency_days,
    ROUND(AVG(frequency), 1)                              AS avg_orders,
    ROUND(SUM(monetary), 0)                               AS revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS pct_revenue
FROM rfm_sql
GROUP BY segment
ORDER BY revenue DESC;

-- ---------------------------------------------------------------------
-- Query 3: Monthly revenue with month-over-month growth
-- Concepts: STRFTIME for date bucketing, LAG() window function
-- ---------------------------------------------------------------------
WITH monthly AS (
    SELECT STRFTIME('%Y-%m', InvoiceDate) AS month,
           SUM(Revenue)                   AS revenue,
           COUNT(DISTINCT Invoice)        AS orders
    FROM sales
    GROUP BY month
)
SELECT month,
       ROUND(revenue, 0) AS revenue,
       orders,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- ---------------------------------------------------------------------
-- Query 4: Repeat-purchase rate by country (min. 20 customers)
-- Concepts: nested aggregation, HAVING
-- ---------------------------------------------------------------------
WITH per_customer AS (
    SELECT CustomerID, Country, COUNT(DISTINCT Invoice) AS orders
    FROM sales
    WHERE CustomerID IS NOT NULL
    GROUP BY CustomerID, Country
)
SELECT Country,
       COUNT(*)                                                  AS customers,
       ROUND(100.0 * SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate_pct
FROM per_customer
GROUP BY Country
HAVING COUNT(*) >= 20
ORDER BY repeat_rate_pct DESC;
