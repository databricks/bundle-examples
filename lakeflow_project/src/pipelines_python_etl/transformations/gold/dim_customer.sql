-- Please edit the sample below

CREATE MATERIALIZED VIEW gold_dim_customer AS
SELECT
    cust.c_custkey                      as customer_key,
    cust.c_name                         as customer_name,
    cust.c_address                      as customer_address,
    cust.c_phone                        as customer_phone,
    cust.c_mktsegment                   as customer_segment,
    coalesce(nat.n_name, 'Unknown')     as customer_nation,
    coalesce(reg.r_name, 'Unknown')     as customer_region
FROM
    silver_customer cust
LEFT JOIN
    silver_nation nat ON cust.c_nationkey = nat.n_nationkey
LEFT JOIN
    silver_region reg ON nat.n_regionkey = reg.r_regionkey