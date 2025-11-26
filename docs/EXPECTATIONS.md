# Data Quality Expectations

This document describes the three types of data quality expectations used in the silver layer transformations.

## Expectation Types

### 1. `expectations_warn`
- **Behavior**: Logs warnings when expectations are violated, but allows data through
- **DLT Decorator**: `@dlt.expect_all()`
- **Use Case**: For non-critical quality checks where you want visibility but don't want to block or drop data
- **Example**: Optional field validation, data quality monitoring

```json
"expectations_warn": {
  "valid_mktsegment": "c_mktsegment IN ('AUTOMOBILE', 'BUILDING', 'FURNITURE', 'HOUSEHOLD', 'MACHINERY')",
  "positive_retailprice": "p_retailprice > 0"
}
```

### 2. `expectations_fail_update`
- **Behavior**: Fails the entire pipeline update if expectations are violated
- **DLT Decorator**: `@dlt.expect_all_or_fail()`
- **Use Case**: For critical business rules that must be met for the pipeline to complete successfully
- **Example**: Regulatory requirements, data integrity constraints

```json
"expectations_fail_update": {
  "valid_discount": "l_discount >= 0 AND l_discount <= 1",
  "valid_region": "r_name IN ('AFRICA', 'AMERICA', 'ASIA', 'EUROPE', 'MIDDLE EAST')"
}
```

### 3. `expectations_drop_row`
- **Behavior**: Drops individual rows that don't meet the expectations, but allows the pipeline to continue
- **DLT Decorator**: `@dlt.expect_all_or_drop()`
- **Use Case**: For data cleansing where invalid rows should be excluded from the dataset
- **Example**: NULL checks, required field validation, data type constraints

```json
"expectations_drop_row": {
  "valid_phone": "c_phone IS NOT NULL AND LENGTH(c_phone) > 0",
  "positive_quantity": "l_quantity > 0"
}
```

## Configuration Example

Complete example from `silver_tables_config.json`:

```json
{
  "source": "bronze.lineitem",
  "destination": "lineitem",
  "primary_keys": ["l_orderkey", "l_linenumber"],
  "description": "Cleaned line item fact table",
  "tags": ["fact", "tpch", "cleaned"],
  "expectations_drop_row": {
    "positive_quantity": "l_quantity > 0",
    "positive_extendedprice": "l_extendedprice > 0"
  },
  "expectations_fail_update": {
    "valid_discount": "l_discount >= 0 AND l_discount <= 1",
    "valid_tax": "l_tax >= 0"
  },
  "expectations_warn": {
    "valid_dates": "l_shipdate >= l_commitdate"
  }
}
```

## Decision Matrix

| Situation | Expectation Type |
|-----------|------------------|
| Critical business rule violation should stop pipeline | `expectations_fail_update` |
| Invalid data should be excluded from results | `expectations_drop_row` |
| Want to monitor quality but not impact data flow | `expectations_warn` |
| NULL in required field | `expectations_drop_row` |
| Value outside valid range (enum) | `expectations_fail_update` or `expectations_drop_row` |
| Suspicious but possibly valid data | `expectations_warn` |

## Primary Key Validation

Note: Primary key NULL checks are automatically applied as `expectations_drop_row` by the framework and don't need to be specified in the configuration.

```python
@dlt.expect_all_or_drop({f"{pk}_not_null": f"{pk} IS NOT NULL" for pk in primary_keys})
```

## Legacy Support

The generic `expectations` field is still supported for backward compatibility and is treated as `expectations_drop_row`.
