import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
import os
import google.generativeai as genai

# --- AI SETUP ---
# For safety, I'm making this an input in the sidebar so you don't leak it in code
st.sidebar.header("🔑 AI Authentication")
api_key = st.sidebar.text_input("AIzaSyB4I393bG8M37USl_ew96JQNPT--0XCPTY", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- CONFIG & SCRAPER ---
FAMOUS_STOCKS = {
    "NVIDIA": "NVDA", "Tesla": "TSLA", "Apple": "AAPL", 
    "Microsoft": "MSFT", "Amazon": "AMZN", "Google": "GOOGL", 
    "Meta": "META", "Netflix": "NFLX", "AMD": "AMD", "Reliance": "RELIANCE.NS"
}

def log_data(ticker, sentiment):
    log_file = "market_history.csv"
    time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame([[time_stamp, ticker, sentiment]], columns=['Timestamp', 'Ticker', 'Sentiment'])
    if not os.path.isfile(log_file): new_data.to_csv(log_file, index=False)
    else: new_data.to_csv(log_file, mode='a', header=False, index=False)
    return pd.read_csv(log_file)

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
st.title("🤖 AI Market Sentinel (Direction 2)")

choice = st.sidebar.selectbox("Select Target Stock:", list(FAMOUS_STOCKS.keys()))
target_ticker = FAMOUS_STOCKS[choice]

if st.sidebar.button("Execute AI Analysis"):
    if not api_key:
        st.error("❌ Please enter your Gemini API Key in the sidebar first!")
    else:
        with st.spinner("Analyzing market psychology..."):
            df = get_news(target_ticker)
            if df is not None:
                avg_s = df['Sentiment'].mean()
                hist_df = log_data(target_ticker, avg_s)
                
                # Visuals
                c1, c2 = st.columns(2)
                with c1:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=avg_s, 
                          title={'text': f"{choice} Sentiment"}, gauge={'axis':{'range':[-1,1]}}))
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.subheader("📈 History")
                    st.line_chart(hist_df[hist_df['Ticker']==target_ticker].set_index('Timestamp')['Sentiment'])
                
                # THE AI ANALYSIS
                st.divider()
                st.subheader("🕵️ Chief Analyst Insight")
                context = "\n".join(df['Headline'].head(10).tolist())
                prompt = f"As a Wall Street expert, analyze these headlines for {choice}: {context}. Give me 3 bullet points on risk, drivers, and a 24-hour outlook. Be sharp and professional."
                
                response = model.generate_content(prompt)
                st.info(response.text)
                
                st.dataframe(df, use_container_width=True)
