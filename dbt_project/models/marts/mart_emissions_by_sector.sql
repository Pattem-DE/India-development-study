with base as (
    select * from {{ ref('stg_climate_trace') }}
),

final as (
    select
        year,
        sector,
        co2e_100yr_million_tonnes,
        global_rank,

        -- sector share of total emissions that year
        round(
            co2e_100yr_million_tonnes / 
            nullif(sum(co2e_100yr_million_tonnes) over (partition by year), 0) * 100
        , 2) as sector_share_pct,

        -- year over year change
        round(
            co2e_100yr_million_tonnes - 
            lag(co2e_100yr_million_tonnes) over (partition by sector order by year)
        , 4) as yoy_change_mt

    from base
)

select * from final
order by year, sector
