{{
  config(materialized='table')
}}

WITH date_spine AS (
    
    SELECT
        (DATE '2016-01-01' + i * interval '1 day')::DATE AS full_date
    FROM (
        SELECT row_number() over () - 1 as i
        FROM {{ ref('stg_orders') }}
        LIMIT 1200
    )
)

SELECT
    cast(to_char(full_date, 'YYYYMMDD') AS INTEGER) AS date_key,
    full_date,
    extract(day from full_date) AS day,
    to_char(full_date, 'Day') AS day_name,
    extract(dow from full_date) AS day_of_week,
    extract(doy from full_date) AS day_of_year,
    extract(week from full_date) AS week_of_year,
    extract(month from full_date) AS month,
    to_char(full_date, 'Month') AS month_name,
    extract(quarter from full_date) AS quarter,
    extract(year from full_date) AS year,
    case when extract(dow from full_date) in (0, 6) then true else false end AS is_weekend
from date_spine

union all

select
    -1 as date_key,
    null as full_date,
    null as day,
    'Unknown' as day_name,
    null as day_of_week,
    null as day_of_year,
    null as week_of_year,
    null as month,
    'Unknown' as month_name,
    null as quarter,
    null as year,
    null as is_weekend