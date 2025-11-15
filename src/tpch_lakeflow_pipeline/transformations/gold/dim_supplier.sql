-- Supplier dimension table with explicit schema and surrogate key

CREATE MATERIALIZED VIEW ${gold_catalog}.${gold_schema}.dim_supplier (
    supplier_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) COMMENT 'Surrogate key for supplier dimension',
    supplier_key BIGINT COMMENT 'Natural key from source system',
    supplier_name STRING COMMENT 'Supplier name',
    supplier_address STRING COMMENT 'Supplier mailing address',
    supplier_phone STRING COMMENT 'Supplier phone number',
    supplier_nation STRING COMMENT 'Supplier nation name',
    supplier_region STRING COMMENT 'Supplier region name',
    supplier_acctbal DECIMAL(15,2) COMMENT 'Supplier account balance',
    load_timestamp TIMESTAMP COMMENT 'Timestamp when record was loaded'
)
COMMENT 'Supplier dimension table with enriched attributes'
TBLPROPERTIES (
    'quality' = 'gold',
    'layer' = 'dimension',
    'delta.enableChangeDataFeed' = 'true'
)
AS
SELECT
    sup.s_suppkey                      as supplier_key,
    sup.s_name                         as supplier_name,
    sup.s_address                      as supplier_address,
    sup.s_phone                        as supplier_phone,
    coalesce(nat.n_name, 'Unknown')    as supplier_nation,
    coalesce(reg.r_name, 'Unknown')    as supplier_region,
    sup.s_acctbal                      as supplier_acctbal,
    current_timestamp()                as load_timestamp
FROM
    ${silver_catalog}.${silver_schema}.supplier sup
LEFT JOIN
    ${silver_catalog}.${silver_schema}.nation nat ON sup.s_nationkey = nat.n_nationkey
LEFT JOIN
    ${silver_catalog}.${silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey