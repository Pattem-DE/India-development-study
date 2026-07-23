import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))
from features import get_upi_monthly_features, get_yearly_development_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")

st.set_page_config(page_title="India Development Study", page_icon="🇮🇳", layout="wide")

st.title("🇮🇳 India Development Study")
st.markdown("""
A data-driven look at how India transformed economically and digitally between 2015-2025.

**Why this study matters:** India went from a largely cash-based, low-internet economy to
building the world's largest real-time digital payments network, all in about a decade.
This project uses real government and public data to answer three concrete questions:
is digital payment growth still accelerating, is the economy growing "cleaner" as it grows
bigger, and what distinct chapters does India's growth story actually break into?
""")

tab1, tab2, tab3 = st.tabs(["📈 UPI Payment Forecast", "🌍 Growth vs Pollution", "🕰️ India's Growth Chapters"])

# ============================================================
# TAB 1: UPI FORECAST
# ============================================================
with tab1:
    st.header("How Fast Will Digital Payments Keep Growing?")

    st.markdown("""
    **What this is:** UPI (Unified Payments Interface) is India's mobile payment system,
    similar to Venmo or Zelle, but used at a national scale for everything from paying a
    street vendor to settling business invoices. This model forecasts how many transactions
    will happen per month over the next year.

    **Why it matters for a business or policy audience:** If you're a bank, a fintech company,
    or a government planner, knowing whether digital payment adoption is still accelerating,
    or starting to plateau, directly affects infrastructure investment, staffing, and product
    decisions. A forecast like this is the kind of number that shows up in board decks and
    budget planning.

    **The technique:** Facebook's Prophet library, a time-series forecasting tool built for
    exactly this kind of business data (a clear trend, seasonal patterns, and the need for
    a reliable forward-looking number, not just a historical chart).
    """)

    months_ahead = st.slider("Months to forecast ahead", 3, 24, 12, key="upi_slider")

    upi_model = joblib.load(os.path.join(MODEL_DIR, "upi_forecaster.joblib"))
    upi_metrics = joblib.load(os.path.join(MODEL_DIR, "upi_forecaster_metrics.joblib"))
    df_hist = get_upi_monthly_features()

    future = upi_model.make_future_dataframe(periods=months_ahead, freq='MS')
    forecast = upi_model.predict(future)

    col1, col2, col3 = st.columns(3)
    col1.metric("Forecasting Method", "Prophet (Meta/Facebook)")
    col2.metric("Forecast Accuracy", f"{upi_metrics['avg_mape']:.2f}% avg error",
                help="On average, predictions are within this percentage of the real number, based on testing against real historical months the model never saw during training.")
    col3.metric("Most Recent Month's Volume", f"{df_hist['volume_mn'].iloc[-1]:,.0f}M transactions")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist['month_date'], y=df_hist['volume_mn'],
                              mode='lines', name='Actual (historical)', line=dict(color='#1f77b4', width=2)))
    future_only = forecast[forecast['ds'] > df_hist['month_date'].max()]
    fig.add_trace(go.Scatter(x=future_only['ds'], y=future_only['yhat'],
                              mode='lines', name='Forecast (predicted)', line=dict(color='#ff7f0e', width=2, dash='dash')))
    fig.add_trace(go.Scatter(
        x=pd.concat([future_only['ds'], future_only['ds'][::-1]]),
        y=pd.concat([future_only['yhat_upper'], future_only['yhat_lower'][::-1]]),
        fill='toself', fillcolor='rgba(255,127,14,0.15)',
        line=dict(color='rgba(255,255,255,0)'), name='Uncertainty range'
    ))
    fig.update_layout(title="Monthly UPI Transactions: What Happened vs What's Predicted Next",
                       xaxis_title="Month", yaxis_title="Transactions per month (in millions)",
                       hovermode='x unified', height=500)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 For engineers: methodology & the debugging journey"):
        st.markdown(f"""
        **Evaluation method:** {upi_metrics['evaluation_method']}

        **Journey to this model:** {upi_metrics['history']}
        """)

# ============================================================
# TAB 2: GDP vs EMISSIONS DECOUPLING
# ============================================================
with tab2:
    st.header("Is India's Growth Getting Cleaner?")

    st.markdown("""
    **What "emissions" means here:** This tracks greenhouse gas emissions, mainly carbon
    dioxide (CO2) and similar gases from power plants, factories, vehicles, and farming, the
    pollution most responsible for climate change. Data comes from Climate TRACE, an
    independent global emissions-tracking project.

    **The real question:** As any country's economy grows, it typically produces more
    pollution too. But does it have to grow at the same rate? A country whose economy grows
    faster than its emissions is called "decoupled", it's finding ways to produce more value
    with proportionally less environmental cost. This matters to investors, sustainability
    analysts, and policymakers deciding whether a country's growth is environmentally
    sustainable long-term, not just economically strong.

    **Why this study is useful:** Instead of guessing or relying on political claims, this
    measures the actual relationship using real GDP and emissions data, a concrete,
    checkable answer rather than an opinion.
    """)

    emissions_metrics = joblib.load(os.path.join(MODEL_DIR, "emissions_trend_metrics.joblib"))
    df_yearly = get_yearly_development_features()

    st.success(f"**Finding:** {emissions_metrics['verdict']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Economic Growth (2015-2024)", f"+{emissions_metrics['gdp_total_growth']:.1f}%",
                help="Total growth in India's GDP (the size of the economy) over this period.")
    col2.metric("Pollution Growth (2015-2024)", f"+{emissions_metrics['emissions_total_growth']:.1f}%",
                help="Total growth in greenhouse gas emissions over the same period.")
    col3.metric("Efficiency Improvement", f"{abs(emissions_metrics['pct_change']):.1f}% less pollution per $",
                help="How much less pollution is produced per dollar of economic output, compared to 2015.")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_yearly['year'], y=df_yearly['gdp_trillion_usd'],
                               mode='lines+markers', name='Economy Size (Trillion USD)',
                               line=dict(color='#2ca02c', width=3), yaxis='y1'))
    fig2.add_trace(go.Scatter(x=df_yearly['year'], y=df_yearly['emissions_intensity'],
                               mode='lines+markers', name='Pollution per $ of Economy',
                               line=dict(color='#d62728', width=3, dash='dot'), yaxis='y2'))
    fig2.update_layout(
        title="Economy Size (growing) vs Pollution Efficiency (falling is good)",
        xaxis_title="Year",
        yaxis=dict(title="Economy Size (Trillion USD)", side='left'),
        yaxis2=dict(title="Emissions per $ of GDP (lower is cleaner)", side='right', overlaying='y'),
        hovermode='x unified', height=500, legend=dict(orientation='h', y=-0.2)
    )
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📋 For engineers: methodology"):
        st.markdown(f"""
        **Emissions intensity** = total CO2-equivalent emissions divided by GDP (trillion USD),
        a standard economic metric for pollution efficiency.

        **Trend slope:** {emissions_metrics['slope']:.2f} per year (R squared = {emissions_metrics['r2']:.3f})
        """)

# ============================================================
# TAB 3: DEVELOPMENT ERAS
# ============================================================
with tab3:
    st.header("The 3 Chapters of India's Growth Story")

    st.markdown("""
    **What this shows:** Rather than us deciding in advance where one "era" of India's
    development ends and another begins, this uses a machine learning technique
    (K-Means clustering) to group years together based on how similar their economic and
    digital conditions actually were. The computer finds the natural chapters, we don't
    impose them.

    **Why this matters:** It's an unbiased way to answer "when did India's digital economy
    actually take off?", useful for anyone telling India's growth story to investors,
    students, or in a business case, backed by data rather than a guess.

    **The 3 chapters the data revealed:**
    - 🏗️ **Foundation Era (2015-2016):** Low internet use, UPI didn't exist yet, a
      traditional, mostly cash-based economy.
    - 📱 **Digital Transition (2017-2020):** UPI launches and scales fast, internet access
      nearly triples, the economy starts shifting online.
    - 🚀 **Mature Digital Economy (2021-2024):** Internet and mobile payments are mainstream,
      UPI is now a core part of daily life, growth continues to compound.
    """)

    eras_labels_map = joblib.load(os.path.join(MODEL_DIR, "eras_labels.joblib"))
    eras_model_obj = joblib.load(os.path.join(MODEL_DIR, "eras_clustering.joblib"))
    eras_scaler_obj = joblib.load(os.path.join(MODEL_DIR, "eras_scaler.joblib"))
    eras_features_list = joblib.load(os.path.join(MODEL_DIR, "eras_features.joblib"))
    eras_metrics_data = joblib.load(os.path.join(MODEL_DIR, "eras_metrics.joblib"))

    df_eras = get_yearly_development_features()
    df_eras['upi_volume_mn'] = df_eras['upi_volume_mn'].fillna(0)

    X = df_eras[eras_features_list]
    X_scaled = eras_scaler_obj.transform(X)
    clusters = eras_model_obj.predict(X_scaled)
    df_eras['era_name'] = [eras_labels_map[c] for c in clusters]

    era_colors = {"Foundation Era": "#8c8c8c", "Digital Transition": "#ff9800", "Mature Digital Economy": "#1f77b4"}

    col1, col2 = st.columns(2)
    col1.metric("How Distinct Are These Eras?", f"{eras_metrics_data['silhouette_score']:.3f} / 1.0",
                help="A score measuring how well-separated these groupings are. 1.0 would be perfectly distinct groups, 0.4 is a moderate, honestly-reported separation given only 10 years of data.")
    col2.metric("Factors Considered", len(eras_metrics_data['features_used']))

    fig3 = go.Figure()
    for era in df_eras['era_name'].unique():
        era_df = df_eras[df_eras['era_name'] == era]
        fig3.add_trace(go.Scatter(x=era_df['year'], y=era_df['gdp_trillion_usd'],
                                   mode='markers+lines', name=era,
                                   marker=dict(size=14, color=era_colors.get(era, '#999')),
                                   line=dict(color=era_colors.get(era, '#999'), width=1, dash='dot')))
    fig3.update_layout(title="Economy Size by Year, Colored by Growth Chapter",
                       xaxis_title="Year", yaxis_title="Economy Size (Trillion USD)",
                       hovermode='x unified', height=450)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("What Defines Each Chapter (Average Values)")

    profile = df_eras.groupby('era_name')[eras_features_list + ['year']].mean().round(2)
    profile_display = profile.rename(columns={
        'gdp_trillion_usd': 'Economy Size ($ Trillion)',
        'internet_users_pct': 'Internet Users (% of population)',
        'mobile_per_100': 'Mobile Subscriptions (per 100 people)',
        'emissions_intensity': 'Pollution per $ of Economy',
        'year': 'Average Year'
    })
    st.dataframe(profile_display, use_container_width=True)

    with st.expander("📋 For engineers: methodology"):
        st.markdown(f"""
        **Features used:** {", ".join(eras_metrics_data['features_used'])}

        **Note:** {eras_metrics_data['note']}
        """)

st.markdown("---")
st.caption("Data sources: World Bank, NPCI (via Kaggle), Climate TRACE, UPI historical data (2016-2025)")
