import streamlit as st
from agent import run_quant_agent
from tools import get_stock_metrics, get_news
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
import yfinance as yf
import re

# =========================
# 🎨 PAGE CONFIG
# =========================
st.set_page_config(page_title="QuantInsight-AI", layout="wide")

# =========================
# 🎯 HEADER
# =========================
st.markdown("""
<h1 style='margin-bottom:0;'>QuantInsight-AI</h1>
<p style='color:gray; margin-top:0;'>Real-time stock analysis dashboard</p>
""", unsafe_allow_html=True)

st.markdown("---")

# =========================
# 📌 SIDEBAR INPUT
# =========================
with st.sidebar:
    st.header("Input")
    tickers = st.text_input("Enter Stock Tickers", "AAPL, TSLA")
    analyze = st.button("Analyze")

# =========================
# 🚀 MAIN LOGIC
# =========================
if analyze:

    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        st.markdown(f"### Analyzing: {', '.join(ticker_list)}")

        results = []
        analysis_map = {}

        # =========================
        # 🔄 PROCESS EACH TICKER
        # =========================
        for ticker in ticker_list:

            data = get_stock_metrics(ticker)

            if not data or "error" in data:
                st.warning(f"Skipping {ticker}")
                continue

            with st.spinner(f"Analyzing {ticker}..."):
                result = run_quant_agent(ticker)

            analysis_map[ticker] = result

            match = re.search(r'Risk Score:\s*(\d+)', result)
            score = int(match.group(1)) if match else 50

            results.append({
                "Ticker": ticker,
                "Price": float(data["price"]),
                "RSI": float(data["rsi"]),
                "MA50": float(data["ma50"]),
                "Risk Score": score
            })

        if not results:
            st.error("No valid tickers found")
            st.stop()

        df = pd.DataFrame(results)

        # =========================
        # 📊 METRICS ROW
        # =========================
        st.markdown("## Overview")

        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Price", round(df["Price"].mean(), 2))
        col2.metric("Avg RSI", round(df["RSI"].mean(), 2))
        col3.metric("Avg Risk", round(df["Risk Score"].mean(), 2))

        st.markdown("---")

        # =========================
        # 📋 TABLE
        # =========================
        st.markdown("## Comparison Table")
        st.dataframe(df, use_container_width=True)

        # =========================
        # 📊 BAR CHART
        # =========================
        fig = px.bar(
            df,
            x="Ticker",
            y="Risk Score",
            color="Risk Score",
            color_continuous_scale="RdYlGn_r",
            title="Risk Comparison"
        )

        fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # =========================
        # 📈 PRICE CHARTS
        # =========================
        st.markdown("## Price Trends")

        for ticker in df["Ticker"]:
            stock = yf.Ticker(ticker)
            df_price = stock.history(period="3mo")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_price.index,
                y=df_price["Close"],
                name=ticker
            ))

            fig.update_layout(
                template="plotly_dark",
                margin=dict(l=20, r=20, t=30, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # =========================
        # 🧠 INSIGHTS (NEW FEATURE)
        # =========================
        st.markdown("## Insights")

        avg_risk = df["Risk Score"].mean()

        if avg_risk > 70:
            st.error("Overall portfolio shows high risk.")
        elif avg_risk > 40:
            st.warning("Moderate risk across selected stocks.")
        else:
            st.success("Stocks appear relatively stable.")

        st.markdown("---")

        # =========================
        # 📄 DETAILED ANALYSIS
        # =========================
        st.markdown("## Detailed Analysis")

        for ticker in df["Ticker"]:
            st.markdown(f"### {ticker}")

            result = analysis_map.get(ticker, "")

            match = re.search(r'Risk Score:\s*(\d+)', result)
            score = int(match.group(1)) if match else 50

            if score > 70:
                color = "red"
                label = "High Risk"
            elif score > 40:
                color = "orange"
                label = "Moderate Risk"
            else:
                color = "green"
                label = "Low Risk"

            st.metric("Risk Score", f"{score}%")
            st.markdown(f"**Status:** :{color}[{label}]")

            # =========================
            # 📰 NEWS
            # =========================
            st.markdown("#### Latest News")

            news = get_news(ticker)

            if news:
                for headline in news.split(".")[:3]:
                    if headline.strip():
                        st.markdown(f"- {headline.strip()}")
            else:
                st.markdown("- No recent news available")

            # =========================
            # 🧠 AI OUTPUT
            # =========================
            st.markdown("#### AI Reasoning")
            st.code(result)

    else:
        st.warning("Please enter at least one stock ticker")
