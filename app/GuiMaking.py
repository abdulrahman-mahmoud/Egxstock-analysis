
import os
import sys
import plotly.express as px
import pandas as pd
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from analyzer import EgxAnalyzer
from scraper import EgxScraper
from vizulliztion import EgxVisualization

#------------------------------------------------------------------------
#                              streamlit 
#-------------------------------------------------------------------------

def loader():
    analyzer = EgxAnalyzer(DATA_DIR)

    if not analyzer.load_data():
        return None,None,None
    
    analyzer.clean()

    analyzer.checker()

    viz = EgxVisualization(analyzer)
    scraper = EgxScraper()

    return analyzer, viz, scraper


st.set_page_config(page_title="EGX Market", layout="wide")
st.sidebar.title("EGX Market")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Scraping", "Company analysis", "Network analysis", "Gainers & Losers", "Sector"]
)

analyzer, viz, scraper = loader()

if analyzer is None:
    st.error("Could not load data. Please check if raw.csv and stock_data.csv exist in the data folder.")
    st.stop()

if page == "Overview":
    st.title("EGX Market Overview")
    st.info("This dashboard analyzes 32 Shariah-compliant companies on the EGX from June to December 2025. Using 4,640 records from Yahoo Finance and African Markets, it evaluates stock performance, risk (volatility), and sector-level trends to provide deep financial insights into the Egyptian market's behavior")
    c1 , c2 , c3 = st.columns(3)
    c1.metric("Total Companies", analyzer.df["Company"].nunique())
    c2.metric("Total Data Points", len(analyzer.df))
    c3.metric("Sectors Covered", len(analyzer.SECTORS))
    st.subheader("Recent Market Data")
    st.dataframe(analyzer.df.head(10), use_container_width=True)


elif page == "Scraping":
    st.title("Scraper")

    start = st.date_input("Start")
    end = st.date_input("End")

    if st.button("Yahoo Api"):

        df = scraper.api(start.isoformat(),end.isoformat())

        if not df.empty:
            scraper.save_csv(df, os.path.join(DATA_DIR, "raw.csv"))
            st.rerun()
            st.success("Saved")

    elif st.button("African Markets"):

        df = scraper.african_markets_scraper()

        if not df.empty:
            scraper.save_csv(df, os.path.join(DATA_DIR, "raw.csv"))
            st.rerun()
            st.success("Saved")

elif page == "Company analysis":

    st.title("Company Analysis")
    names = analyzer.company_names()
    company = st.selectbox("company",names)

    data = analyzer.specific_company(company)

    if data is None:
        st.error("No data")
        st.stop()
    
    c1 ,c2 ,c3 ,c4 = st.columns(4)
    c1.metric("Sector", data["sector"])
    c2.metric("YTD", data["ytd"])
    c3.metric("Close", f"{data['latest']['close']:.2f}")
    c4.metric("Volatility", f"{data['risk']['annualized_volatility']:.2f}%")

    df_plot = analyzer.df[analyzer.df["Company"] == company]

    fig = px.line(df_plot, x="Date", y="Close", title=f"{company} Price Trend")

    st.plotly_chart(fig, use_container_width=True)

    st.title("Monthly Volatility (Risk)")

    MonthVol = viz.plot_rolling_volatility(company)

    st.plotly_chart(MonthVol,use_container_width=True)    

    st.title("Volatility (Risk)")

    vol = viz.PlotVolatility()
    st.pyplot(vol,use_container_width=True)


elif page == "Network analysis":
    
    st.title("Market Network Analysis")
    st.write("Graph visualizing company clusters grouped by their sectors.")
    st.pyplot(viz.networkx_sector())


elif page == "Sector":
    st.title("Sector Performance")
    st.write("Visualizes the performance of a 10,000 EGP investment per sector.")
    sector_plt = viz.PlotSector_Growth()

    st.plotly_chart(sector_plt, use_container_width=True)


elif page == "Gainers & Losers":

    st.title("Top Gainers & Losers")
    col1, col2 = st.columns(2)

    with col1:
        st.pyplot(viz.plot_gainers(5))

    with col2:
        st.pyplot(viz.plot_losers(5))
        
    monthly_perf = analyzer.get_monthly()

    top_companies = analyzer.df["Company"].value_counts().head(15).index.tolist()
    fig = viz.heatmap(top_companies, monthly_perf)
    
    st.title("Heatmap - Monthly Returns")

    st.pyplot(fig)
    
        


