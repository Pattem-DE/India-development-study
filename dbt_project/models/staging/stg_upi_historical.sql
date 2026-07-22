with source as (
    select * from {{ source('raw', 'raw_upi_historical') }}
),

cleaned as (
    select
        cast(month_date as date)          as month_date,
        cast(banks_live_on_upi as int)    as banks_live_on_upi,
        round(volume_mn, 2)               as volume_mn,
        round(value_cr, 2)                as value_cr,
        round(avg_txn_value_inr, 2)       as avg_txn_value_inr,
        round(mom_growth_volume_pct, 4)   as mom_growth_volume_pct,
        round(mom_growth_value_pct, 4)    as mom_growth_value_pct,
        ingested_at
    from source
    where month_date is not null
)

select * from cleaned
order by month_date
