{{
  config(materialized='table')
}}

WITH customer_addresses AS (
SELECT 
    customer_unique_id,
    customer_city,
    customer_state,
    customer_zip_code_prefix,
    MAX(customer_id) AS tie_break_customer_id,
    COUNT(*) AS address_frequency
FROM 
    {{ ref('stg_customers') }}
GROUP BY 1,2,3,4
), 

ranked_addresses AS 

(
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id 
            ORDER BY address_frequency DESC, tie_break_customer_id DESC
        ) AS address_rank
    FROM 
        customer_addresses
),

representative_address as (
    SELECT
        customer_unique_id,
        customer_city,
        customer_state,
        customer_zip_code_prefix
    FROM 
        ranked_addresses
    WHERE address_rank = 1
)

SELECT
    ROW_NUMBER() OVER (ORDER BY ra.customer_unique_id) AS customer_key,
    ra.customer_unique_id,
    ra.customer_city,
    ra.customer_state,
    ra.customer_zip_code_prefix,
    geo.latitude,
    geo.longitude
FROM representative_address ra
LEFT JOIN {{ ref('stg_geolocation') }} geo
    ON ra.customer_zip_code_prefix = geo.zip_code_prefix