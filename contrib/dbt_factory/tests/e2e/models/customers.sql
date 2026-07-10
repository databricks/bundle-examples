-- Base model, no upstream deps. Literal rows keep the e2e fast and workspace-agnostic.
select 1 as customer_id, 'Alice' as customer_name
union all select 2, 'Bob'
union all select 3, 'Charlie'
union all select 4, 'Diana'
union all select 5, 'Eve'
