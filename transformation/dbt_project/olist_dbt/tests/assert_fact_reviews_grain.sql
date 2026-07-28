select review_id, order_id, count(*)
from {{ ref('fact_reviews') }}
group by review_id, order_id
having count(*) > 1