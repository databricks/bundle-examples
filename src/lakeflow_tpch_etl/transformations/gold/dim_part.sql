-- Please edit the sample below

CREATE MATERIALIZED VIEW ${gold_catalog}.${gold_schema}.dim_part AS
SELECT
    part.p_partkey                      as part_key,
    part.p_mfgr                         as part_mfgr,
    part.p_brand                        as part_brand,
    part.p_type                         as part_type,
    part.p_size                         as part_size,
    part.p_container                    as part_container,
    part.p_retailprice                  as part_retailprice
FROM
    ${silver_catalog}.${silver_schema}.part part