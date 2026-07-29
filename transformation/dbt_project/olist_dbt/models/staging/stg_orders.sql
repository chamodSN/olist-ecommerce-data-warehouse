select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    cast(round(delivery_delay_days) as integer) as delivery_delay_days
from {{ source('silver', 'orders') }}