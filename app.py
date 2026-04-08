import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import os
from google import genai

# --- CONFIG ---
FAMOUS_STOCKS = {
    "NVIDIA": "NVDA", "Tesla": "TSLA", "Apple": "AAPL", 
    "Microsoft": "MSFT", "Amazon": "AMZN", "Google": "GOOGL", 
    "Meta": "META", "Netflix": "NFLX", "AMD": "AMD", "Reliance": "RELIANCE.NS"
}

# --- FUNCTIONS ---
def get_news(ticker):
    url = f'https://finviz.com/quote.ashx?t={ticker}'
    
    # Advanced Headers to mimic a real browser perfectly
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        # Using a session is more stable
        session = requests.Session()
        r = session.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return None
            
        soup = BeautifulSoup(r.content, 'html.parser')
        news_table = soup.find(id='news-table')
        
        if not news_table:
            return None
            
        data = []
        for row in news_table.find_all('tr')[:15]:
            a_tag = row.find('a')
            if not a_tag: continue
            text = a_tag.get_text()
            score = TextBlob(text).sentiment.polarity
            data.append([text, score])
        return pd.DataFrame(data, columns=['Headline', 'Sentiment'])
    except Exception as e:
        print(f"Scraping Error: {e}")
        return None

# --- UI ---
st.set_page_config(page_title="Market Mood AI", layout="wide")
st.title("🤖 AI Market Sentinel (Direction 2)")

# Sidebar for API Key
st.sidebar.header("🔑 Authentication")
user_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

choice = st.sidebar.selectbox("Select Target Stock:", list(FAMOUS_STOCKS.keys()))
target_ticker = FAMOUS_STOCKS[choice]

if st.sidebar.button("Execute AI Analysis"):
    if not user_key:
        st.sidebar.error("⚠️ Enter API Key first!")
    else:
        with st.spinner("🤖 Calling the Chief Analyst..."):
            # 1. Get Data
            df = get_news(target_ticker)
            
            if df is not None:
                avg_s = df['Sentiment'].mean()
                
                # 2. Visuals
                c1, c2 = st.columns([1, 1])
                with c1:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_s, 
                          title={'text': f"{choice} Sentiment"}, gauge={'axis':{'range':[-1,1]}}))
                    st.plotly_chart(fig, use_container_width=True)
                
                # 3. AI Analysis (New 2026 Syntax)
                st.divider()
                st.subheader("🕵️ Chief Analyst Insight")
                try:
                    client = genai.Client(api_key=user_key)
                    context = "\n".join(df['Headline'].head(10).tolist())
                    
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=f"Analyze these headlines for {choice}: {context}. Give 3 ruthless bullet points on risk, drivers, and 24h outlook."
                    )
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI Error: Make sure your API key is valid. {e}")
                
                # 4. Raw Data
                st.subheader("Latest Headlines")
                st.dataframe(df, use_container_width=True)
            else:
                st.error("Failed to fetch news. Finviz might be blocking the request.")
