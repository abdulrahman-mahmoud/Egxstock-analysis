import os
import sys
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(REPO_DIR, "data")

if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from app.analyzer import EgxAnalyzer
from app.vizulliztion import EgxVisualization
from app.scraper import EgxScraper

st.set_page_config(
    page_title="EGX Market Intelligence",
    layout="wide",
)

st.sidebar.title("EGX Market")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Scraping",
        "Sector Analysis",
        "Company Analysis",
        "Stock Screener",
        "Gainers & Losers",
        "Network Analysis",
        "3D Analysis",
        "Summary",
    ],
)


@st.cache_resource
def loader(raw_mtime, stock_mtime, scraper_mtime):
    analyzer = EgxAnalyzer(DATA_DIR)

    if not analyzer.load_data():
        return None, None, None

    analyzer.clean()
    analyzer.checker()

    viz = EgxVisualization(analyzer)
    scraper = EgxScraper()
    return analyzer, viz, scraper


raw_path = os.path.join(DATA_DIR, "raw.csv")
stock_path = os.path.join(DATA_DIR, "stock_data.csv")
scraper_path = os.path.join(APP_DIR, "ingestion", "scraper.py")

raw_mtime = os.path.getmtime(raw_path) if os.path.exists(raw_path) else None
stock_mtime = os.path.getmtime(stock_path) if os.path.exists(stock_path) else None
scraper_mtime = os.path.getmtime(scraper_path) if os.path.exists(scraper_path) else None

analyzer, viz, scraper = loader(raw_mtime, stock_mtime, scraper_mtime)

if analyzer is None:
    st.error("Missing dataset files (raw.csv / stock_data.csv)")
    st.stop()


if page == "Overview":
    st.title("EGX Market Overview")
    st.caption(f"Egyptian Stock Market Analysis of {analyzer.df['Company'].nunique()} Companies")

    c1, c2, c3 = st.columns(3)
    c1.metric("Companies", analyzer.df["Company"].nunique())
    c2.metric("Records", len(analyzer.df))
    c3.metric("Sectors", len(analyzer.sector_map or {}))

    st.write(
        """
        ## Project Overview
        This project analyzes the Egyptian Stock Exchange (EGX)

        It helps us understand:
        - How companies perform in the market
        - Market trends over time
        - Differences between sectors

        The project includes:
        - Collecting stock data
        - Cleaning and organizing it
        - Calculating financial indicators
        - Building visual charts for analysis

        Made by **Abdel-Rahman & Omar Saeed**.
        """
    )

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
                scraper.save_csv(df, os.path.join(DATA_DIR, "stock_data.csv"))
                st.success("Data saved")
                st.rerun()

elif page == "Company Analysis":
    st.title("Company Analysis")

    company = st.selectbox("Select Company", analyzer.company_names())

    data = analyzer.specific_company(company)
    decision = analyzer.company_decision(company)

    if data is None:
        st.error("No data available for this company")
        st.stop()

    ticker = analyzer.get_ticker(company)

    st.subheader(f"{company} ({ticker})")
    st.caption("Price behavior, performance metrics, and risk profile")

    if decision is not None:
        st.markdown("### Decision Summary")
        d1, d2, d3 = st.columns(3)
        d1.metric("Decision Score", f"{decision['decision_score']}/100")
        d2.metric("Signal", decision["signal"])
        d3.metric("Timing Hint", decision["timing_hint"])

        st.info(f"Reason: {decision['reason']}")

        if decision["red_flags"]:
            st.warning("Red Flags: " + " | ".join(decision["red_flags"]))
        else:
            st.success("Red Flags: No major risk alerts from the current rule set")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sector", data["sector"])
    c2.metric("YTD Return", data["ytd"])
    c3.metric("Last Price", f"{data['latest']['close']:.2f}")
    c4.metric("Volatility", f"{data['risk']['annualized_volatility']:.2f}%")
    c5.metric("Ticker", ticker)

    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("Price Trend")
        st.plotly_chart(viz.plot_company_price(company), use_container_width=True)

    with right:
        st.subheader("Monthly Returns")
        st.plotly_chart(viz.plot_company_monthly_returns(company), use_container_width=True)

    st.divider()
    st.subheader("Risk Analysis")
    st.plotly_chart(viz.plot_rolling_volatility(company), use_container_width=True)
    st.divider()

elif page == "Stock Screener":
    st.title("Stock Screener")
    st.caption("Filter EGX stocks by score, risk, momentum, and sector strength")

    ranked = analyzer.rank_companies()

    if ranked.empty:
        st.error("No ranked stocks available")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        only_low_risk = st.checkbox("Low Risk")
    with c2:
        only_high_momentum = st.checkbox("High Momentum")
    with c3:
        only_strong_sector = st.checkbox("Strong Sector")
    with c4:
        only_top_score = st.checkbox("Top Score")

    filtered = analyzer.screen_companies(
        max_volatility=25 if only_low_risk else None,
        min_one_month_return=5 if only_high_momentum else None,
        min_sector_return=2 if only_strong_sector else None,
        min_score=70 if only_top_score else None,
    )

    top_n = st.slider("Rows to show", min_value=5, max_value=30, value=10)

    s1, s2, s3 = st.columns(3)
    s1.metric("Matching Stocks", len(filtered))
    s2.metric("Top Score", int(filtered["Decision Score"].max()) if not filtered.empty else 0)
    s3.metric("Average Score", round(filtered["Decision Score"].mean(), 1) if not filtered.empty else 0.0)

    st.dataframe(filtered.head(top_n), use_container_width=True)

    if not filtered.empty:
        st.subheader("Top Candidates Snapshot")
        st.dataframe(
            filtered[["Company", "Signal", "Timing Hint", "Reason", "Red Flags"]].head(5),
            use_container_width=True,
        )

elif page == "Network Analysis":
    st.title("Market Network Analysis")
    st.caption("Sector relationships and market risk structure")
    st.divider()
    st.subheader("Sector Network Graph")
    st.plotly_chart(viz.networkx_sector(), use_container_width=True)
    st.divider()
    st.subheader("Market Volatility Distribution")
    st.plotly_chart(viz.PlotVolatility(), use_container_width=True)

elif page == "Sector Analysis":
    st.title("Sector Performance")
    st.plotly_chart(viz.PlotSector_Growth(), use_container_width=True)

elif page == "Gainers & Losers":
    st.title("Market Leaders")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top Gainers")
        st.plotly_chart(viz.plot_gainers(5), use_container_width=True)

    with c2:
        st.subheader("Top Losers")
        st.plotly_chart(viz.plot_losers(5), use_container_width=True)

    st.divider()
    st.subheader("Monthly Heatmap")

    monthly_perf = analyzer.get_monthly()
    top_companies = analyzer.top_activity_companies(15)

    st.plotly_chart(viz.heatmap(top_companies, monthly_perf), use_container_width=True)

elif page == "3D Analysis":
    st.title("3D Market Analysis")
    st.subheader("Monthly Return, Volatility and Volume 3D View")
    st.plotly_chart(viz.ThreeD_plt(), use_container_width=True)

elif page == "Summary":
    st.title("Market Summary")

    ranked = analyzer.rank_companies()

    if ranked.empty:
        st.error("No summary data available")
        st.stop()

    best_stock = ranked.iloc[0]
    risky_stock = ranked.iloc[-1]

    st.subheader("Best Buy Idea Right Now")
    st.success(
        f"{best_stock['Company']} looks like an attractive stock to buy now. "
        f"It has a decision score of {int(best_stock['Decision Score'])}/100, "
        f"the signal is {best_stock['Signal'].lower()}, and the trend is {best_stock['Timing Hint'].lower()}."
    )

    st.write(
        f"Why: {best_stock['Reason']}. "
        f"The stock has a 1 month return of {best_stock['1M Return (%)']:.2f}% "
        f"and a 3 month return of {best_stock['3M Return (%)']:.2f}%."
    )

    st.divider()

    st.subheader("Stock To Be Careful With")
    st.warning(
        f"{risky_stock['Company']} looks weaker right now. "
        f"It has a decision score of {int(risky_stock['Decision Score'])}/100, "
        f"with a {risky_stock['Signal'].lower()} signal and a {risky_stock['Timing Hint'].lower()} trend."
    )

    st.write(
        f"Why: {risky_stock['Reason']}. "
        f"Its volatility is {risky_stock['Volatility (%)']:.2f}% "
        f"and its max drawdown is {risky_stock['Max Drawdown (%)']:.2f}%."
    )

    st.divider()

    st.subheader("Quick Market Read")
    top_candidates = ranked.head(3)["Company"].tolist()
    st.info(
        "The market summary is now focused on decision support. "
        f"Based on the current model, the strongest names are {', '.join(top_candidates)}."
    )
