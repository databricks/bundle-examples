-- Customer dimension table with explicit schema and surrogate key

CREATE MATERIALIZED VIEW ${gold_catalog}.${gold_schema}.dim_customer (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) COMMENT 'Surrogate key for customer dimension',
    customer_key BIGINT COMMENT 'Natural key from source system',
    customer_name STRING COMMENT 'Customer name',
    customer_address STRING COMMENT 'Customer mailing address',
    customer_phone STRING COMMENT 'Customer phone number',
    customer_segment STRING COMMENT 'Market segment',
    customer_nation STRING COMMENT 'Customer nation name',
    customer_region STRING COMMENT 'Customer region name',
    customer_acctbal DECIMAL(15,2) COMMENT 'Customer account balance',
    load_timestamp TIMESTAMP COMMENT 'Timestamp when record was loaded'
)
COMMENT 'Customer dimension table with enriched attributes'
TBLPROPERTIES (
    'quality' = 'gold',
    'layer' = 'dimension',
    'delta.enableChangeDataFeed' = 'true'
)
AS
SELECT
    cust.c_custkey                      as customer_key,
    cust.c_name                         as customer_name,
    cust.c_address                      as customer_address,
    cust.c_phone                        as customer_phone,
    cust.c_mktsegment                   as customer_segment,
    coalesce(nat.n_name, 'Unknown')     as customer_nation,
    coalesce(reg.r_name, 'Unknown')     as customer_region,
    cust.c_acctbal                      as customer_acctbal,
    current_timestamp()                 as load_timestamp
FROM
    ${silver_catalog}.${silver_schema}.customer cust
LEFT JOIN
    ${silver_catalog}.${silver_schema}.nation nat ON cust.c_nationkey = nat.n_nationkey
LEFT JOIN
    ${silver_catalog}.${silver_schema}.region reg ON nat.n_regionkey = reg.r_regionkey