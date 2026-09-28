# Executive Summary: Customer Value, Churn Risk & Revenue Outlook

**Scope:** UK online gift wholesaler · Dec 2009 – Dec 2011 · 1.0M clean transactions · £19.3M revenue · 5,852 identified customers

## Key findings
1. **Revenue is highly concentrated.** The top 20% of customers produce 77% of revenue. The "Champions" segment (850 customers, 15%) alone produces 53%. The UK is 85% of revenue.
2. **The first repeat purchase is the critical moment.** Only ~21% of new customers buy again the following month, and 28% never return. Customers who place 2+ orders spend on average £3,826 vs £343 for one-time buyers.
3. **£1.47M of historic spend sits with lapsing high-value customers** ("At Risk" and "Can't Lose Them", 828 customers).
4. **Churn can be predicted.** A logistic regression model ranks customers by 90-day churn risk with ROC-AUC 0.77 on an unseen future quarter. The riskiest 10% churn at 79% vs a 49% average. The strongest warning sign is a customer who is *overdue relative to their own normal buying rhythm*.
5. **Next-quarter revenue outlook: ~£1.9M** (80% range £1.35M–£2.54M) for mid-Dec 2011 to early Mar 2012, reflecting the post-Christmas seasonal low. The method's backtest error on the previous quarter was 12% (WAPE) with −0.9% bias.

## Recommendations
| Priority | Action | Target |
|---|---|---|
| 1 | **Protect Champions:** loyalty tier / account management, no blanket discounts | 850 customers, 53% of revenue |
| 2 | **Weekly churn call list:** contact the top-20 customers by *revenue at risk* (probability × value) | £442K next-quarter revenue at risk |
| 3 | **Second-purchase journey:** onboarding offer timed 2–4 weeks after first order | New customers & Potential Loyalists |
| 4 | **Win-back campaign** for "Can't Lose Them" (72 former top buyers) | £0.5M historic spend |
| 5 | **Plan inventory and cash for the Q4 peak** using the weekly forecast and its range | Sep–Nov revenue ≈ 2× spring |

## Approach
Data quality audit and cleaning (Python) → RFM scoring and segmentation → K-Means clustering (validated against RFM) → cohort retention → churn classification with point-in-time features and out-of-time validation → weekly revenue forecast (harmonic regression + seasonal-naive ensemble, benchmarked against baselines) → SQL rebuild with reconciliation → Power BI dashboard.

## Key assumptions
- **Churn** = no purchase in the next 90 days, among customers who bought in the prior 365 days.
- Transactions without a Customer ID (13% of revenue) are included in company revenue and the forecast but excluded from customer analysis.
- Cancellations are treated as returns; bulk orders cancelled in full were removed as data-entry errors.
- The Christmas shutdown and seasonal pattern repeat each year.

## Limitations
- Only two years of history, so seasonality is learnt from a single repeat.
- Churn probabilities are over-stated in the Q4 peak (seasonal shift). The model *ranks* well, but probabilities would need seasonal recalibration.
- Customer-level £ predictions from ML did not beat a simple average-quarter rule, so the simpler rule is used for customer value.
- No external drivers (pricing, promotions, macro-economy) or cost/margin data, so revenue is analysed rather than profit.
- The first cohort (Dec 2009) contains pre-existing customers, so its retention is overstated.
