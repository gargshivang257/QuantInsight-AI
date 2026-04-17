from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
import yfinance as yf
import re
from datetime import datetime, timedelta

from agent import run_quant_agent
from tools import get_stock_metrics, get_news

# =========================
#  PRO-LEVEL STYLING (THE "LIMIT BREAKER")
# =========================
st.set_page_config(page_title="QuantInsight | Pro Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Main Background & Font */
    .main { background-color: #0e1117; font-family: 'Inter', sans-serif; }
   
    /* Custom Card Styling */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
    }
    .stMetric:hover { transform: translateY(-5px); border-color: #00d4ff; }
   
    /* Header Gradient */
    .header-text {
        font-weight: 800;
        background: -webkit-linear-gradient(#00d4ff, #005fb8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 42px;
    }
   
    /* Status Labels */
    .status-low { color: #00ff88; font-weight: bold; }
    .status-mod { color: #ffaa00; font-weight: bold; }
    .status-high { color: #ff4b4b; font-weight: bold; }
   
    /* Sidebar Cleanup */
    .css-1d391kg { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# =========================
#  SIDEBAR & CONFIG
# =========================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2108/2108625.png", width=80)
    st.markdown("<h2 style='color:#00d4ff;'>Terminal Config</h2>", unsafe_allow_html=True)
   
    tickers = st.text_input("Asset Tickers", value="AAPL, TSLA, NVDA", help="Comma separated tickers (e.g. BTC-USD, MSFT)")
    timeframe = st.select_slider("Chart Horizon", options=["1mo", "3mo", "6mo", "1y"], value="3mo")
   
    st.markdown("---")
    analyze_btn = st.button(" EXECUTE ANALYSIS", use_container_width=True)
   
    st.info("Terminal v2.4.0-Stable | Connected to Live Quant Agent")

# =========================
#  HEADER SECTION
# =========================
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.markdown('<p class="header-text">QuantInsight Pro</p>', unsafe_allow_html=True)
    st.markdown(f"**Session:** `{datetime.now().strftime('%Y-%m-%d %H:%M')}` | **Market Status:** `OPEN`")

# =========================
#  CORE ENGINE
# =========================
if analyze_btn:
    if not tickers:
        st.toast("Error: No tickers provided", icon="❌")
        st.stop()

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
   
    # Progress UI
    progress_bar = st.progress(0)
    status_text = st.empty()
   
    results = []
    analysis_map = {}

    for idx, ticker in enumerate(ticker_list):
        status_text.text(f"Fetching Data: {ticker}")
        data = get_stock_metrics(ticker)
       
        if not data or "error" in data:
            st.warning(f"Engine Failure: {ticker} - Skipping")
            progress_bar.progress((idx + 1) / len(ticker_list))
            continue

        status_text.text(f"Agent Logic: {ticker}")
        agent_result = run_quant_agent(ticker)
        analysis_map[ticker] = agent_result

        # Extract Risk Score
        match = re.search(r'Risk Score:\s*(\d+)', agent_result)
        score = int(match.group(1)) if match else 50
       
        # Safely get dictionary keys
        results.append({
            "Ticker": ticker,
            "Price": float(data.get("price", 0.0)),
            "RSI": float(data.get("rsi", 0.0)),
            "MA50": float(data.get("ma50", 0.0)),
            "Risk Score": score,
            "News": get_news(ticker) or ""
        })
        progress_bar.progress((idx + 1) / len(ticker_list))

    if not results:
        status_text.empty()
        progress_bar.empty()
        st.error("Terminal could not resolve any valid tickers.")
        st.stop()

    df = pd.DataFrame(results)
    status_text.empty()
    progress_bar.empty()

    # =========================
    #  EXECUTIVE OVERVIEW
    # =========================
    st.markdown("### 📊 Portfolio Intelligence")
    m1, m2, m3, m4 = st.columns(4)
   
    avg_risk = df["Risk Score"].mean()
    risk_color = "normal" if avg_risk < 60 else "inverse"
   
    m1.metric("Coverage", len(df))
    m2.metric("Mean RSI", f"{df['RSI'].mean():.2f}", delta_color=risk_color)
    m3.metric("Aggregate Risk", f"{avg_risk:.1f}%")
    m4.metric("Engine Latency", "1.2s", delta="Optimum")

    # =========================
    #  DUAL-TAB INTERFACE
    # =========================
    tab_market, tab_tech, tab_ai = st.tabs(["📈 Market View", "📉 Technical Terminal", "🤖 AI Quant Reasoning"])

    with tab_market:
        col_table, col_risk = st.columns([2, 1])
       
        with col_table:
            st.markdown("**Active Asset Comparison**")
            st.dataframe(df.drop(columns=["News"]), use_container_width=True)
           
        with col_risk:
            fig_risk = px.bar(df, x="Ticker", y="Risk Score", color="Risk Score",
                             color_continuous_scale="RdYlGn_r", title="Risk Exposure Index")
            fig_risk.update_layout(template="plotly_dark", height=300, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_risk, use_container_width=True)

    with tab_tech:
        st.markdown("**High-Fidelity Price Action**")
        for ticker in df["Ticker"]:
            with st.expander(f"TECHNICAL CHART: {ticker}", expanded=True):
                stock = yf.Ticker(ticker)
                hist = stock.history(period=timeframe)
               
                # FIX: Handle empty yfinance responses gracefully
                if hist.empty:
                    st.warning(f"No charting data available for {ticker} in the selected timeframe.")
                    continue
               
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    name="Price"
                )])
               
                # FIX: Ensure enough data points exist before calculating/plotting MA
                if len(hist) >= 20:
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].rolling(window=20).mean(),
                                             line=dict(color='#00d4ff', width=1.5), name='MA20'))
               
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False,
                                 height=400, margin=dict(t=0, b=0, l=10, r=10))
                st.plotly_chart(fig, use_container_width=True)

    with tab_ai:
        for ticker in df["Ticker"]:
            st.markdown(f"#### 分析报告 (Analysis Report): {ticker}")
            c1, c2 = st.columns([1, 2])
           
            with c1:
                score = df[df['Ticker'] == ticker]['Risk Score'].values[0]
                status_class = "status-low" if score < 40 else "status-mod" if score < 70 else "status-high"
                label = "SAFE" if score < 40 else "CAUTION" if score < 70 else "DANGER"
               
                st.markdown(f"**Quant Score:** <span class='{status_class}'>{score}%</span>", unsafe_allow_html=True)
                st.markdown(f"**Security Rating:** <span class='{status_class}'>{label}</span>", unsafe_allow_html=True)
               
                # st.write("**Recent News Sentiments:**")
                # news_txt = df[df['Ticker'] == ticker]['News'].values[0]
               
                # # Ensure it's a valid string before splitting
                # if isinstance(news_txt, str) and news_txt.strip():
                #     for line in news_txt.split('.')[:4]:
                #         if len(line.strip()) > 5: st.caption(f"• {line.strip()}")
                # else:
                #     st.caption("No sentiment data available.")
                st.write("**Recent News Sentiments:**")
                news_txt = df[df['Ticker'] == ticker]['News'].values[0]
                if isinstance(news_txt, str) and news_txt.strip():
                    # Split by newlines, regular periods, or Japanese full stops
                    split_news = re.split(r'[\n.。]+', news_txt)
                    
                    # Track valid lines so we only show up to 4
                    valid_lines = [line.strip() for line in split_news if len(line.strip()) > 15]
                    
                    for line in valid_lines[:4]:
                        st.caption(f"• {line}")
                else:
                    st.caption("No sentiment data available.")

            with c2:
                st.markdown(" **AI Intelligence Feed**")
                st.info(analysis_map[ticker])

# =========================
#  IDLE STATE
# =========================
else:
    st.divider()
    st.markdown("""
        ### Welcome to the Quant Terminal
        Enter tickers in the sidebar and click **Execute** to begin real-time data ingestion.
        The system will trigger:
        - 📡 Live Price Scraping
        - 📉 Technical Indicator Calculation (RSI/MA50)
        - 🧠 Neural-Agent Sentiment Analysis
    """)
