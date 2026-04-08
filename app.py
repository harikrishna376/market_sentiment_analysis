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
    headers = {'user-agent': 'Mozilla/5.0'}
    url = f'https://finviz.com/quote.ashx?t={ticker}'
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        news_table = soup.find(id='news-table')
        data = []
        for row in news_table.find_all('tr')[:15]:
            text = row.a.get_text()
            score = TextBlob(text).sentiment.polarity
            data.append([text, score])
        return pd.DataFrame(data, columns=['Headline', 'Sentiment'])
    except: return None

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
