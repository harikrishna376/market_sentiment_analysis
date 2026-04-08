import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import plotly.express as px

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

# 2. THE SCRAPER FUNCTION
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
            headline_text = a_tag.get_text()
            timestamp = row.td.get_text().strip() if row.td else "N/A"
            score = TextBlob(headline_text).sentiment.polarity
            if ticker.lower() not in headline_text.lower(): score *= 0.3 
            for word, boost in multipliers.items():
                if word in headline_text.lower(): score *= boost
            score = max(min(score, 1), -1)
            headlines.append([timestamp, headline_text, score])
        return pd.DataFrame(headlines, columns=['Time', 'Headline', 'Sentiment'])
    except: return None

# 3. STREAMLIT UI SETUP
st.set_page_config(page_title="Market Mood AI", layout="wide")
st.title("📈 Market Mood AI: Elite Sentiment Analysis")
# --- THE KNOWLEDGE HUB ---
with st.expander("ℹ️ How to read the Sentiment Scale"):
    st.markdown("""
    ### The Sentiment Scale (-1 to 1)
    This AI analyzes financial headlines and assigns a score based on emotional weight and market impact.
    
    | Value | Market Meaning | Example Headline |
    | :--- | :--- | :--- |
    | **1.0** | **🚀 Extreme Bullish** | "NVIDIA profits skyrocket 200% as AI demand surges." |
    | **0.5** | **✅ Strongly Positive** | "Apple beats earnings expectations; shares rise." |
    | **0.0** | **😐 Neutral / Flat** | "Microsoft announces routine board meeting." |
    | **-0.5** | **⚠️ Strongly Negative** | "Amazon faces heavy fine over data privacy." |
    | **-1.0** | **📉 Extreme Bearish** | "Market crash imminent as tech stocks plunge." |
    
    **Note:** We use a *Weighted Engine* that boosts the importance of keywords like 'AI', 'Profit', and 'Loss'.
    """)

# SIDEBAR SELECTION
st.sidebar.header("Control Panel")
choice = st.sidebar.selectbox("Select a Famous Stock:", list(FAMOUS_STOCKS.keys()))
target_ticker = FAMOUS_STOCKS[choice]

if st.sidebar.button("Run Mission"):
    df = get_live_news_elite(target_ticker)
    
    if df is not None:
        # GAUGE
        avg_score = df['Sentiment'].mean()
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = avg_score,
            title = {'text': f"{choice} Sentiment Score"},
            gauge = {'axis': {'range': [-1, 1]}, 'bar': {'color': "#00f2fe"}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # HEADLINES TABLE
        st.subheader(f"Latest News for {choice}")
        st.dataframe(df.sort_values(by='Sentiment', ascending=False), use_container_width=True)
    else:
        st.error("Site Blocked or Ticker Invalid. Try again in 1 minute.")
