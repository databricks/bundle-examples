-- Singular test: fails if any order has a negative amount.
select order_id, amount
from {{ ref('orders') }}
where amount < 0
