with base as (
    select * from {{ ref('int_india_yearly') }}
),

final as (
    select
        year,

        -- Economy
        gdp_trillion_usd,
        poverty_rate_pct,
        population,

        -- Digital India
        internet_users_pct,
        mobile_per_100,
        electricity_access_pct,

        -- UPI Payments
        upi_volume_mn,
        upi_value_cr,
        avg_txn_value_inr,
        banks_on_upi,

        -- Emissions
        total_co2e_mt,
        power_co2e_mt,
        transport_co2e_mt,
        manufacturing_co2e_mt,
        agriculture_co2e_mt,

        -- Derived metrics
        round(upi_value_cr / nullif(gdp_trillion_usd, 0) / 1e4, 4)
            as upi_value_as_pct_gdp,

        round(total_co2e_mt / nullif(population, 0) * 1e6, 4)
            as co2e_per_capita_tonnes,

        round((gdp_trillion_usd - lag(gdp_trillion_usd) 
            over (order by year)) 
            / nullif(lag(gdp_trillion_usd) 
            over (order by year), 0) * 100, 2)
            as gdp_yoy_growth_pct

    from base
)

select * from final
order by year
