{% snapshot orders_snapshot %}
{{
    config(
      target_schema=target.schema,
      unique_key='order_id',
      strategy='check',
      check_cols=['amount']
    )
}}
select * from {{ ref('orders') }}
{% endsnapshot %}
