from tools import get_stock_metrics, get_sentiment
from google import genai
import os
import streamlit as st

# Get API key from .env (local) or Streamlit secrets (cloud)
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

# 🔥 ADD THIS SAFETY CHECK
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set")

# Initialize client
client = genai.Client(api_key=api_key)
import time
def safe_generate(prompt):
    for i in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print("Retrying...", i+1)
            time.sleep(5)
    
    return "Error: API unavailable"

def compute_base_risk(data):
    risk = 50

    # RSI contribution
    if data["rsi"] > 70:
        risk += 20
    elif data["rsi"] < 30:
        risk -= 10

    # Trend contribution
    if data["price"] < data["ma50"]:
        risk += 15
    else:
        risk -= 5

    return max(0, min(100, risk))

def run_quant_agent(ticker):
    print(f"\n--- Fetching metrics for {ticker} ---")

    stock_data = get_stock_metrics(ticker)

    base_risk = compute_base_risk(stock_data)

    # Improved realistic news
    #news_content = f"{ticker} is experiencing fluctuating prices with cautious investor sentiment and mixed earnings outlook."
    from tools import get_news
    news_content = get_news(ticker)
    if not news_content:
      news_content = f"{ticker} has mixed market sentiment."
    sentiment_data = get_sentiment(news_content)

    prompt = f"""
    ROLE: Senior Quantitative Financial Analyst

    TASK: Analyze the given stock and provide a risk assessment.

    DATA:
    Stock Metrics: {stock_data}
    Sentiment: {sentiment_data}
    Base Risk Score (quant model): {base_risk}%

    REQUIREMENTS:
    1. Provide a Risk Score (0–100%).
    2. Provide Final Verdict: BUY, HOLD, or SELL.
    3. Base reasoning on:
       - RSI
       - Price vs Moving Average
       - Sentiment

    OUTPUT FORMAT (STRICT):
    Risk Score: <number>%
    Final Verdict: <BUY/HOLD/SELL>

    Reasoning:
    - RSI insight
    - Trend insight
    - Sentiment insight
    """

    result = safe_generate(prompt)

    if "Error" in result:
        # 🔥 NEW dynamic fallback

        rsi = stock_data["rsi"]
        price = stock_data["price"]
        ma = stock_data["ma50"]

        risk = 50

        if rsi > 70:
          risk += 20
        elif rsi < 30:
          risk -= 10

        if price < ma:
          risk += 15
        else:
          risk -= 5

        risk = max(0, min(100, risk))

        verdict = "SELL" if risk > 65 else "HOLD" if risk > 40 else "BUY"

        return f"""
    Risk Score: {risk}%

    Final Verdict: {verdict}

    Reasoning:
    - RSI = {rsi}
    - Price vs MA indicates {'downtrend' if price < ma else 'uptrend'}
    - Sentiment fallback used
    """
    else:
      return result

# --- Execution ---
if __name__ == "__main__":
    ticker_to_scan = input("Enter Stock Ticker (e.g., TSLA): ").upper()
    result = run_quant_agent(ticker_to_scan)

    print("\n--- AGENT VERDICT ---")
    print(result)