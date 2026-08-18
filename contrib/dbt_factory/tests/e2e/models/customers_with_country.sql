-- Downstream of the countries seed: exercises seed -> model gating.
select
    c.customer_id,
    c.customer_name,
    co.country_code,
    co.country_name
from {{ ref('customers') }} c
cross join (
    select country_code, country_name from {{ ref('countries') }} where country_code = 'DE'
) co
