with source as (
    select * from {{ source('raw', 'raw_climate_trace') }}
),

cleaned as (
    select
        year,
        country_code,
        sector,
        rank                                        as global_rank,
        round(co2_tonnes / 1e6, 4)                 as co2_million_tonnes,
        round(ch4_tonnes / 1e6, 4)                 as ch4_million_tonnes,
        round(n2o_tonnes / 1e6, 4)                 as n2o_million_tonnes,
        round(co2e_100yr_tonnes / 1e6, 4)          as co2e_100yr_million_tonnes,
        ingested_at
    from source
    where year is not null
)

select * from cleaned
order by year, sector
