with source as (
    select * from {{ source('raw', 'raw_world_bank') }}
),

cleaned as (
    select
        year,
        country_code,
        country_name,
        indicator_code,
        indicator_name,
        round(cast(value as double), 4) as value,
        ingested_at
    from source
    where value is not null
      and year is not null
)

select * from cleaned
order by year, indicator_name
