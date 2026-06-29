DROP TABLE IF EXISTS top_products_monthly CASCADE;
DROP TABLE IF EXISTS top_sellers_monthly CASCADE;
DROP TABLE IF EXISTS monthly_kpis CASCADE;
DROP TABLE IF EXISTS fact_reviews CASCADE;
DROP TABLE IF EXISTS fact_payments CASCADE;
DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_geolocation CASCADE;
DROP TABLE IF EXISTS dim_seller CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;

CREATE TABLE dim_customer (
    customer_display_id TEXT PRIMARY KEY,
    customer_unique_display_id TEXT,
    zip_code_prefix INTEGER,
    city TEXT,
    state TEXT,
    original_customer_id TEXT,
    original_customer_unique_id TEXT
);

CREATE TABLE dim_product (
    product_display_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_category_name_english TEXT,
    product_name_length DOUBLE PRECISION,
    product_description_length DOUBLE PRECISION,
    product_photos_qty DOUBLE PRECISION,
    product_weight_g DOUBLE PRECISION,
    product_length_cm DOUBLE PRECISION,
    product_height_cm DOUBLE PRECISION,
    product_width_cm DOUBLE PRECISION,
    original_product_id TEXT
);

CREATE TABLE dim_seller (
    seller_display_id TEXT PRIMARY KEY,
    zip_code_prefix INTEGER,
    city TEXT,
    state TEXT,
    original_seller_id TEXT
);

CREATE TABLE dim_geolocation (
    zip_code_prefix INTEGER,
    city TEXT,
    state TEXT,
    avg_lat DOUBLE PRECISION,
    avg_lng DOUBLE PRECISION
);

CREATE TABLE dim_date (
    date DATE PRIMARY KEY,
    date_key INTEGER,
    year INTEGER,
    quarter TEXT,
    month INTEGER,
    month_name TEXT,
    year_month TEXT,
    day INTEGER,
    day_name TEXT,
    week_of_year INTEGER,
    is_weekend BOOLEAN
);

CREATE TABLE fact_orders (
    order_display_id TEXT PRIMARY KEY,
    customer_display_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    original_order_id TEXT,
    original_customer_id TEXT,
    purchase_date DATE,
    purchase_year_month TEXT,
    delivery_days DOUBLE PRECISION,
    late_delivery_days DOUBLE PRECISION,
    is_late_delivery INTEGER,
    CONSTRAINT fk_fact_orders_customer
        FOREIGN KEY (customer_display_id) REFERENCES dim_customer(customer_display_id)
);

CREATE TABLE fact_order_items (
    order_display_id TEXT,
    order_item_id INTEGER,
    product_display_id TEXT,
    seller_display_id TEXT,
    shipping_limit_date TIMESTAMP,
    price DOUBLE PRECISION,
    freight_value DOUBLE PRECISION,
    original_order_id TEXT,
    original_product_id TEXT,
    original_seller_id TEXT,
    item_revenue DOUBLE PRECISION,
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_display_id) REFERENCES fact_orders(order_display_id),
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_display_id) REFERENCES dim_product(product_display_id),
    CONSTRAINT fk_order_items_seller
        FOREIGN KEY (seller_display_id) REFERENCES dim_seller(seller_display_id)
);

CREATE TABLE fact_payments (
    order_display_id TEXT,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value DOUBLE PRECISION,
    original_order_id TEXT,
    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_display_id) REFERENCES fact_orders(order_display_id)
);

CREATE TABLE fact_reviews (
    review_row_id BIGSERIAL PRIMARY KEY,
    review_display_id TEXT,
    order_display_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    original_review_id TEXT,
    original_order_id TEXT,
    CONSTRAINT fk_reviews_order
        FOREIGN KEY (order_display_id) REFERENCES fact_orders(order_display_id)
);

CREATE TABLE monthly_kpis (
    purchase_year_month TEXT PRIMARY KEY,
    revenue DOUBLE PRECISION,
    orders INTEGER,
    unique_customers INTEGER,
    late_deliveries INTEGER,
    delivered_orders INTEGER,
    avg_delivery_days DOUBLE PRECISION,
    late_delivery_pct DOUBLE PRECISION
);

CREATE TABLE top_sellers_monthly (
    purchase_year_month TEXT,
    seller_display_id TEXT,
    revenue DOUBLE PRECISION,
    orders INTEGER,
    units_sold INTEGER
);

CREATE TABLE top_products_monthly (
    purchase_year_month TEXT,
    product_display_id TEXT,
    product_category_name_english TEXT,
    revenue DOUBLE PRECISION,
    orders INTEGER,
    units_sold INTEGER
);

CREATE INDEX idx_fact_orders_month ON fact_orders(purchase_year_month);
CREATE INDEX idx_fact_orders_purchase_date ON fact_orders(purchase_date);
CREATE INDEX idx_fact_order_items_order ON fact_order_items(order_display_id);
CREATE INDEX idx_fact_payments_order ON fact_payments(order_display_id);
CREATE INDEX idx_fact_reviews_order ON fact_reviews(order_display_id);
CREATE INDEX idx_top_sellers_month ON top_sellers_monthly(purchase_year_month);
CREATE INDEX idx_top_products_month ON top_products_monthly(purchase_year_month);
