-- Base model, no upstream deps.
select 1 as order_id, 1 as customer_id, 50.00 as amount
union all select 2, 2, 75.50
union all select 3, 1, 30.00
union all select 4, 3, 100.00
union all select 5, 4, 25.00
union all select 6, 5, 60.00
union all select 7, 2, 45.00
union all select 8, 1, 90.00
