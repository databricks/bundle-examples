-- Downstream of two models: exercises model -> model dependencies.
with customers as (select * from {{ ref('customers') }}),
     orders as (select * from {{ ref('orders') }})
select
    customers.customer_id,
    customers.customer_name,
    count(orders.order_id) as total_orders,
    coalesce(sum(orders.amount), 0) as total_amount
from customers
left join orders on customers.customer_id = orders.customer_id
group by customers.customer_id, customers.customer_name
