import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob
import os
import requests


def get_stock_metrics(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")

        if df.empty:
            return {"error": "Invalid ticker or no data"}

        # Current Price
        current_price = float(round(df["Close"].iloc[-1], 2))

        # Moving Average (50-day)
        df["MA50"] = df["Close"].rolling(window=50).mean()
        ma50 = float(round(df["MA50"].iloc[-1], 2))

        # RSI (14-day)
        delta = df["Close"].diff()

        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        gain_series = pd.Series(gain)
        loss_series = pd.Series(loss)

        avg_gain = gain_series.rolling(window=14).mean()
        avg_loss = loss_series.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        latest_rsi = float(round(rsi.iloc[-1], 2))

        return {
            "price": current_price,
            "rsi": latest_rsi,
            "ma50": ma50
        }

    except Exception as e:
        return {"error": str(e)}


def get_sentiment(text: str):
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            label = "Positive"
        elif polarity < -0.1:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "sentiment": label,
            "score": round(polarity, 2)
        }

    except Exception as e:
        return {"error": str(e)}


def get_news(ticker):
    API_KEY = os.getenv("NEWS_API_KEY")

    trusted_domains = "yahoo.com,bloomberg.com,reuters.com,cnbc.com,wsj.com,marketwatch.com"

    url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&domains={trusted_domains}&sortBy=publishedAt&apiKey={API_KEY}"

    try:
        response = requests.get(url).json()
        articles = response.get("articles", [])

        headlines = []
        for article in articles[:3]:
            title = article.get("title", "")
            if title and title != "[Removed]":
                clean_title = title.rstrip('.')
                headlines.append(clean_title)

        return ". ".join(headlines) + "."

    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return ""