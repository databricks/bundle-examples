-- Please edit the sample below

CREATE MATERIALIZED VIEW ${gold_catalog}.${gold_schema}.dim_supplier AS
SELECT
    sup.s_suppkey                      as supplier_key,
    sup.s_name                         as supplier_name,
    sup.s_address                      as supplier_address,
    sup.s_phone                        as supplier_phone,
    coalesce(nat.n_name, 'Unknown')    as supplier_nation,
    coalesce(reg.r_name, 'Unknown')    as supplier_region
FROM
    ${silver_catalog}.${silver_schema}.supplier sup
LEFT JOIN
    ${silver_catalog}.${silver_schema}.nation nat ON sup.s_nationkey = nat.n_nationkey
LEFT JOIN
    ${silver_catalog}.${silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey