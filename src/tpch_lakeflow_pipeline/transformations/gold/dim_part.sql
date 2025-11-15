-- Part dimension table with explicit schema and surrogate key

CREATE MATERIALIZED VIEW ${gold_catalog}.${gold_schema}.dim_part (
    part_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) COMMENT 'Surrogate key for part dimension',
    part_key BIGINT COMMENT 'Natural key from source system',
    part_name STRING COMMENT 'Part name',
    part_mfgr STRING COMMENT 'Manufacturer',
    part_brand STRING COMMENT 'Brand name',
    part_type STRING COMMENT 'Part type',
    part_size INT COMMENT 'Part size',
    part_container STRING COMMENT 'Container type',
    part_retailprice DECIMAL(18,2) COMMENT 'Retail price',
    load_timestamp TIMESTAMP COMMENT 'Timestamp when record was loaded'
)
COMMENT 'Part dimension table with product attributes'
TBLPROPERTIES (
    'quality' = 'gold',
    'layer' = 'dimension',
    'delta.enableChangeDataFeed' = 'true'
)
AS
SELECT
    part.p_partkey                      as part_key,
    part.p_name                         as part_name,
    part.p_mfgr                         as part_mfgr,
    part.p_brand                        as part_brand,
    part.p_type                         as part_type,
    part.p_size                         as part_size,
    part.p_container                    as part_container,
    part.p_retailprice                  as part_retailprice,
    current_timestamp()                 as load_timestamp
FROM
    ${silver_catalog}.${silver_schema}.part part