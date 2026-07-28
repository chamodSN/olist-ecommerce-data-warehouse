{{
  config(materialized='table')
}}

select
    oi.order_id,
    oi.order_item_id,
    dp.product_key,
    ds.seller_key,
    dc.customer_key,
    coalesce(cast(to_char(o.order_purchase_timestamp, 'YYYYMMDD') as integer), -1) as purchase_date_key,
    coalesce(cast(to_char(oi.shipping_limit_date, 'YYYYMMDD') as integer), -1) as shipping_limit_date_key,
    oi.price,
    oi.freight_value
from {{ ref('stg_order_items') }} oi
inner join {{ ref('stg_orders') }} o
    on oi.order_id = o.order_id
left join {{ ref('dim_products') }} dp
    on oi.product_id = dp.product_id
left join {{ ref('dim_sellers') }} ds
    on oi.seller_id = ds.seller_id
left join {{ ref('stg_customers') }} sc
    on o.customer_id = sc.customer_id
left join {{ ref('dim_customers') }} dc
    on sc.customer_unique_id = dc.customer_unique_id