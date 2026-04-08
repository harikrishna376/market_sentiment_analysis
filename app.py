import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import os

# 1. SETUP THE FAMOUS STOCKS
FAMOUS_STOCKS = {
    "NVIDIA": "NVDA",
    "Tesla": "TSLA",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Google": "GOOGL",
    "Meta": "META",
    "Netflix": "NFLX",
    "AMD": "AMD",
    "Reliance": "RELIANCE.NS"
}

# 2. THE MEMORY ENGINE (Direction 1: Data Persistence)
def log_sentiment_data(ticker, avg_sentiment):
    log_file = "market_history.csv"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = pd.DataFrame([[timestamp, ticker, avg_sentiment]], 
                             columns=['Timestamp', 'Ticker', 'Sentiment'])
    
    if not os.path.isfile(log_file):
        new_entry.to_csv(log_file, index=False)
    else:
        new_entry.to_csv(log_file, mode='a', header=False, index=False)
    
    return pd.read_csv(log_file)

# 3. THE SCRAPER ENGINE
def get_live_news_elite(ticker):
    url = f'https://finviz.com/quote.ashx?t={ticker}'
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36'}
    multipliers = {'ai': 2.5, 'profit': 2.0, 'surge': 2.0, 'loss': 2.5, 'lawsuit': 3.0, 'growth': 1.5}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_table = soup.find(id='news-table')
        if news_table is None: return None
        headlines = []
        for row in news_table.find_all('tr'):
            a_tag = row.find('a')
            if not a_tag: continue
            text = a_tag.get_text()
            timestamp = row.td.get_text().strip() if row.td else "N/A"
            score = TextBlob(text).sentiment.polarity
            if ticker.lower() not in text.lower(): score *= 0.3 
            for word, boost in multipliers.items():
                if word in text.lower(): score *= boost
            score = max(min(score, 1), -1)
            headlines.append([timestamp, text, score])
        return pd.DataFrame(headlines, columns=['Time', 'Headline', 'Sentiment'])
    except: return None

# 4. UI SETUP
st.set_page_config(page_title="Market Mood AI", layout="wide")
st.title("📈 Market Mood AI: Predictive Sentiment Engine")

# Legend/Knowledge Hub
with st.expander("ℹ️ How to read the Sentiment Scale"):
    st.markdown("""
    | Value | Market Meaning | Example |
    | :--- | :--- | :--- |
    | **1.0** | **🚀 Extreme Bullish** | Skyrocketing profits |
    | **0.0** | **😐 Neutral** | Routine news |
    | **-1.0** | **📉 Extreme Bearish** | Market crash/lawsuits |
    """)

# SIDEBAR
st.sidebar.header("Control Panel")
choice = st.sidebar.selectbox("Select Target Stock:", list(FAMOUS_STOCKS.keys()))
target_ticker = FAMOUS_STOCKS[choice]

if st.sidebar.button("Run Mission"):
    df = get_live_news_elite(target_ticker)
    
    if df is not None:
        avg_score = df['Sentiment'].mean()
        
        # LOG DATA FOR DIRECTION 1
        history_df = log_sentiment_data(target_ticker, avg_score)
        
        # COLUMNS FOR GAUGE AND TREND
        col1, col2 = st.columns(2)
        
        with col1:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = avg_score,
                title = {'text': f"Current {choice} Mood"},
                gauge = {'axis': {'range': [-1, 1]}, 'bar': {'color': "#00f2fe"}}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col2:
            st.subheader("📊 Historical Sentiment Trend")
            ticker_history = history_df[history_df['Ticker'] == target_ticker]
            if not ticker_history.empty:
                st.line_chart(ticker_history.set_index('Timestamp')['Sentiment'])
            else:
                st.write("First data point recorded! Run again later to see trends.")

        # RAW DATA
        st.subheader("Latest Headlines")
        st.dataframe(df.sort_values(by='Sentiment', ascending=False), use_container_width=True)
    else:
        st.error("Connection lost. Try again.")
