-- Downstream of a Unity Catalog `samples` source: exercises source -> model and source tests.
select
    o_orderpriority as order_priority,
    count(*) as order_count,
    sum(o_totalprice) as total_price
from {{ source('samples_tpch', 'orders') }}
group by o_orderpriority
