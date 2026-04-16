import streamlit as st
from agent import run_quant_agent
from tools import get_stock_metrics, get_news
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
import yfinance as yf
import re

# =========================
# 🎨 UI Styling
# =========================
st.set_page_config(page_title="Quantsight-AI", layout="wide")

st.markdown("""
<style>
.big-font {
    font-size:28px !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Quant AI Analyst Pro")
st.caption("Real-time AI-powered financial risk intelligence")

# =========================
# 🔤 Input
# =========================
tickers = st.text_input("Enter Stock Tickers (comma separated, e.g., AAPL, TSLA)")

# =========================
# 🚀 Main Logic
# =========================
if st.button("Analyze"):

    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

        st.subheader(f"Analyzing: {', '.join(ticker_list)}")

        results = []
        analysis_map = {}

        # =========================
        # 🔄 PROCESS EACH TICKER
        # =========================
        for ticker in ticker_list:

            data = get_stock_metrics(ticker)

            # skip invalid tickers
            if not data or "error" in data:
                st.warning(f"Skipping {ticker} (invalid or no data)")
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

        # 🚨 If nothing valid
        if not results:
            st.error("No valid tickers found")
            st.stop()

        df = pd.DataFrame(results)

        # =========================
        # 📊 DASHBOARD
        # =========================
        st.markdown("## 📊 Dashboard")
        st.divider()

        # =========================
        # 📊 TABLE
        # =========================
        st.markdown("### 📋 Comparison Table")
        st.dataframe(df, use_container_width=True)

        # =========================
        # 📊 BAR CHART
        # =========================
        fig = px.bar(
            df,
            x="Ticker",
            y="Risk Score",
            color="Risk Score",
            title="📊 Risk Comparison Across Stocks",
            color_continuous_scale="RdYlGn_r"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # =========================
        # 📈 PRICE CHARTS
        # =========================
        st.markdown("## 📈 Price Charts")

        for ticker in df["Ticker"]:   # ✅ FIXED
            stock = yf.Ticker(ticker)
            df_price = stock.history(period="3mo")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_price.index,
                y=df_price["Close"],
                name=ticker
            ))

            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # =========================
        # 📄 DETAILED ANALYSIS
        # =========================
        st.markdown("## 📄 Detailed Analysis")

        for ticker in df["Ticker"]:   # ✅ FIXED
            st.markdown(f"### {ticker}")

            result = analysis_map.get(ticker, "")

            match = re.search(r'Risk Score:\s*(\d+)', result)
            score = int(match.group(1)) if match else 50

            # 🎨 Risk Styling
            if score > 70:
                color = "red"
                emoji = "🔴"
                label = "High Risk"
            elif score > 40:
                color = "orange"
                emoji = "🟠"
                label = "Moderate Risk"
            else:
                color = "green"
                emoji = "🟢"
                label = "Low Risk"

            st.markdown(
                f"<div class='big-font'>{emoji} Risk Score: {score}%</div>",
                unsafe_allow_html=True
            )
            st.markdown(f"**Status:** :{color}[{label}]")

            # =========================
            # 📰 NEWS
            # =========================
            news = get_news(ticker)

            st.markdown("#### 📰 Latest News")

            if news:
                for headline in news.split(".")[:3]:
                    if headline.strip():
                        st.markdown(f"- {headline.strip()}")
            else:
                st.markdown("- No recent news available")

            st.markdown("#### 🧠 AI Reasoning")
            st.markdown(f"```\n{result}\n```")

    else:
        st.warning("Please enter at least one stock ticker")
