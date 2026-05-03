import os
import sys
import plotly.express as px
import pandas as pd
import streamlit as st

# =========================================================
# PATH SETUP
# =========================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from analyzer import EgxAnalyzer
from scraper import EgxScraper
from vizulliztion import EgxVisualization


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="EGX Market Intelligence",
    layout="wide"
)

st.sidebar.title("EGX Market")

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Scraping", "Company Analysis", "Network Analysis", "Gainers & Losers", "Sector Analysis"]
)


# =========================================================
# LOADER
# =========================================================

@st.cache_data
def loader():
    analyzer = EgxAnalyzer(DATA_DIR)

    if not analyzer.load_data():
        return None, None, None

    analyzer.clean()
    analyzer.checker()

    viz = EgxVisualization(analyzer)
    scraper = EgxScraper()

    return analyzer, viz, scraper


analyzer, viz, scraper = loader()

if analyzer is None:
    st.error("Missing dataset files (raw.csv / stock_data.csv)")
    st.stop()


# =========================================================
# OVERVIEW 
# =========================================================

if page == "Overview":

    st.title("EGX Market Overview")

    st.caption("High-level snapshot of Egyptian equity market behavior")

    c1, c2, c3 = st.columns(3)

    c1.metric("Companies", analyzer.df["Company"].nunique())
    c2.metric("Records", len(analyzer.df))
    c3.metric("Sectors", len(analyzer.SECTORS))

    st.divider()

    st.subheader("Market Index (Normalized)")

    market = analyzer.df.groupby("Date")["Close"].mean().reset_index()
    market["Index"] = market["Close"] / market["Close"].iloc[0] * 100

    st.line_chart(market.set_index("Date")["Index"])

    st.divider()

    st.subheader("Sector Distribution")

    st.bar_chart(analyzer.df["Sector"].value_counts())


# =========================================================
# SCRAPING
# =========================================================

elif page == "Scraping":

    st.title("Data Scraping")

    start = st.date_input("Start Date")
    end = st.date_input("End Date")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Yahoo Finance API"):
            df = scraper.api(start.isoformat(), end.isoformat())
            if not df.empty:
                scraper.save_csv(df, os.path.join(DATA_DIR, "raw.csv"))
                st.success("Data saved")
                st.rerun()

    with c2:
        if st.button("African Markets Scraper"):
            df = scraper.african_markets_scraper()
            if not df.empty:
                scraper.save_csv(df, os.path.join(DATA_DIR, "raw.csv"))
                st.success("Data saved")
                st.rerun()


# =========================================================
# COMPANY ANALYSIS 
# =========================================================

elif page == "Company Analysis":

    st.title("Company Analysis")

    company = st.selectbox("Select Company", analyzer.company_names())

    data = analyzer.specific_company(company)

    if data is None:
        st.error("No data available for this company")
        st.stop()

    ticker = analyzer.get_ticker(company)

    st.subheader(f"{company} ({ticker})")

    st.caption("Price behavior, performance metrics, and risk profile")



    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Sector", data["sector"])
    c2.metric("YTD Return", data["ytd"])
    c3.metric("Last Price", f"{data['latest']['close']:.2f}")
    c4.metric("Volatility", f"{data['risk']['annualized_volatility']:.2f}%")
    c5.metric("Ticker", ticker)

    st.divider()

    df_plot = analyzer.df[analyzer.df["Company"] == company].copy()

    # =====================================================
    # PRICE + MONTHLY PERFORMANCE
    # =====================================================

    left, right = st.columns(2)

    with left:
        st.subheader("Price Trend")
        st.plotly_chart(px.line(df_plot, x="Date", y="Close"), use_container_width=True)

    with right:
        st.subheader("Monthly Returns")

        df_plot["Month"] = pd.to_datetime(df_plot["Date"]).dt.to_period("M").astype(str)

        monthly = df_plot.groupby("Month")["Close"].agg(["first", "last"])
        monthly["Return %"] = ((monthly["last"] - monthly["first"]) / monthly["first"]) * 100

        st.bar_chart(monthly["Return %"])

    st.divider()

    # =====================================================
    # RISK 
    # =====================================================

    st.subheader("Risk Analysis")

    st.plotly_chart(viz.plot_rolling_volatility(company), use_container_width=True)

    st.divider()

    st.subheader("Monthly Breakdown Table")

    st.dataframe(monthly)


# =========================================================
# NETWORK ANALYSIS 
# =========================================================

elif page == "Network Analysis":

    st.title("Market Network Analysis")

    st.caption("Sector relationships and market risk structure")

    st.divider()

    st.subheader("Sector Network Graph")
    st.pyplot(viz.networkx_sector())
    
    st.divider()
    
    st.subheader("Market Volatility Distribution")
    st.pyplot(viz.PlotVolatility())


# =========================================================
# SECTOR ANALYSIS
# =========================================================

elif page == "Sector Analysis":

    st.title("Sector Performance")

    st.plotly_chart(viz.PlotSector_Growth(), use_container_width=True)


# =========================================================
# GAINERS & LOSERS
# =========================================================

elif page == "Gainers & Losers":

    st.title("Market Leaders")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top Gainers")
        st.pyplot(viz.plot_gainers(5))

    with c2:
        st.subheader("Top Losers")
        st.pyplot(viz.plot_losers(5))

    st.divider()

    st.subheader("Monthly Heatmap")

    monthly_perf = analyzer.get_monthly()
    top_companies = analyzer.df["Company"].value_counts().head(15).index.tolist()

    st.pyplot(viz.heatmap(top_companies, monthly_perf))