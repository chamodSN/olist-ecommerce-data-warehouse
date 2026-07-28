{{
  config(materialized='table')
}}

select
    row_number() over (order by s.seller_id) as seller_key,
    s.seller_id,
    s.seller_city,
    s.seller_state,
    s.seller_zip_code_prefix,
    geo.latitude,
    geo.longitude
from {{ ref('stg_sellers') }} s
left join {{ ref('stg_geolocation') }} geo
    on s.seller_zip_code_prefix = geo.zip_code_prefix