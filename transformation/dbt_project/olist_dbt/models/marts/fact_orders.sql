{{
  config(materialized='table')
}}

WITH payment_rollup AS (
    SELECT
        order_id,
        sum(payment_value) as total_payment_value,
        count(DISTINCT payment_sequential) AS payment_method_count
    FROM {{ ref('stg_order_payments') }}
    GROUP BY order_id
),

review_rollup AS (
    SELECT
        order_id,
        cast(avg(review_score) as decimal(3,2)) as avg_review_score,
        count(*) as review_count
    FROM {{ ref('stg_order_reviews') }}
    GROUP BY order_id
)

SELECT
    o.order_id,
    dc.customer_key,
    coalesce(cast(to_char(o.order_purchase_timestamp, 'YYYYMMDD') AS INTEGER), -1) AS purchase_date_key,
    coalesce(cast(to_char(o.order_approved_at, 'YYYYMMDD') AS INTEGER), -1) AS approval_date_key,
    coalesce(cast(to_char(o.order_delivered_carrier_date, 'YYYYMMDD') AS INTEGER), -1) AS carrier_date_key,
    coalesce(cast(to_char(o.order_delivered_customer_date, 'YYYYMMDD') AS INTEGER), -1) AS delivery_date_key,
    coalesce(cast(to_char(o.order_estimated_delivery_date, 'YYYYMMDD') AS INTEGER), -1) AS estimated_delivery_date_key,
    o.order_status,
    o.delivery_delay_days,
    coalesce(pr.total_payment_value, 0) as total_payment_value,
    coalesce(pr.payment_method_count, 0) as payment_method_count,
    rr.avg_review_score,
    coalesce(rr.review_count, 0) as review_count
from {{ ref('stg_orders') }} o
left join {{ ref('stg_customers') }} sc
    on o.customer_id = sc.customer_id
left join {{ ref('dim_customers') }} dc
    on sc.customer_unique_id = dc.customer_unique_id
left join payment_rollup pr
    on o.order_id = pr.order_id
left join review_rollup rr
    on o.order_id = rr.order_id