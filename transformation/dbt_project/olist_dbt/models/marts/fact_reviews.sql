{{
  config(materialized='table')
}}

select
    review_id,
    order_id,
    coalesce(cast(to_char(review_creation_date, 'YYYYMMDD') as integer), -1) as review_creation_date_key,
    coalesce(cast(to_char(review_answer_timestamp, 'YYYYMMDD') as integer), -1) as review_answer_date_key,
    review_score
from {{ ref('stg_order_reviews') }}