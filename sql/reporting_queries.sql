-- Last 6 months KPI data for Excel VBA report.
-- Replace '2018-08' with the selected report end month.
WITH last_6_months AS (
    SELECT purchase_year_month
    FROM monthly_kpis
    WHERE purchase_year_month <= '2018-08'
    ORDER BY purchase_year_month DESC
    LIMIT 6
)
SELECT
    k.purchase_year_month,
    k.revenue,
    k.orders,
    k.unique_customers,
    k.late_delivery_pct,
    k.avg_delivery_days
FROM monthly_kpis k
JOIN last_6_months m
    ON k.purchase_year_month = m.purchase_year_month
ORDER BY k.purchase_year_month;

-- Top 10 sellers for selected month.
SELECT
    purchase_year_month,
    seller_display_id,
    revenue,
    orders,
    units_sold
FROM top_sellers_monthly
WHERE purchase_year_month = '2018-08'
ORDER BY revenue DESC
LIMIT 10;

-- Top 10 products for selected month.
SELECT
    purchase_year_month,
    product_display_id,
    product_category_name_english,
    revenue,
    orders,
    units_sold
FROM top_products_monthly
WHERE purchase_year_month = '2018-08'
ORDER BY revenue DESC
LIMIT 10;
