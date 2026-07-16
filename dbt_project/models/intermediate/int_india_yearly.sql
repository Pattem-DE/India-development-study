with world_bank as (
    select
        year,
        max(case when indicator_name = 'gdp_usd' 
            then value end)                         as gdp_usd,
        max(case when indicator_name = 'poverty_rate' 
            then value end)                         as poverty_rate_pct,
        max(case when indicator_name = 'internet_users_pct' 
            then value end)                         as internet_users_pct,
        max(case when indicator_name = 'mobile_subscriptions_per100' 
            then value end)                         as mobile_per_100,
        max(case when indicator_name = 'electricity_access_pct' 
            then value end)                         as electricity_access_pct,
        max(case when indicator_name = 'population' 
            then value end)                         as population
    from {{ ref('stg_world_bank') }}
    group by year
),

emissions as (
    select
        year,
        sum(co2e_100yr_million_tonnes)              as total_co2e_mt,
        max(case when sector = 'power' 
            then co2e_100yr_million_tonnes end)     as power_co2e_mt,
        max(case when sector = 'transportation' 
            then co2e_100yr_million_tonnes end)     as transport_co2e_mt,
        max(case when sector = 'manufacturing' 
            then co2e_100yr_million_tonnes end)     as manufacturing_co2e_mt,
        max(case when sector = 'agriculture' 
            then co2e_100yr_million_tonnes end)     as agriculture_co2e_mt
    from {{ ref('stg_climate_trace') }}
    group by year
),

upi_yearly as (
    select
        extract(year from month_date)               as year,
        sum(volume_mn)                              as upi_volume_mn,
        sum(value_cr)                               as upi_value_cr,
        avg(avg_txn_value_inr)                      as avg_txn_value_inr,
        max(banks_live_on_upi)                      as banks_on_upi
    from {{ ref('stg_upi_historical') }}
    group by extract(year from month_date)
),

joined as (
    select
        wb.year,
        -- Economy
        round(wb.gdp_usd / 1e12, 4)                as gdp_trillion_usd,
        wb.poverty_rate_pct,
        wb.population,
        -- Digital
        wb.internet_users_pct,
        wb.mobile_per_100,
        -- Energy access
        wb.electricity_access_pct,
        -- Payments
        upi.upi_volume_mn,
        upi.upi_value_cr,
        upi.avg_txn_value_inr,
        upi.banks_on_upi,
        -- Emissions
        em.total_co2e_mt,
        em.power_co2e_mt,
        em.transport_co2e_mt,
        em.manufacturing_co2e_mt,
        em.agriculture_co2e_mt
    from world_bank wb
    left join emissions em on wb.year = em.year
    left join upi_yearly upi on wb.year = upi.year
    where wb.year between 2015 and 2024
)

select * from joined
order by year
