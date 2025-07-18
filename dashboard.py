# ======================================================
# 🌍 Dashboard Économie Mondiale - Version PRO Gratuite
# ======================================================
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from transformers import pipeline
from prophet import Prophet

# ==========================
# Config
# ==========================
FINNHUB_API_KEY = d1sua1pr01qhe5rc4vj0d1sua1pr01qhe5rc4vjg
MARKETAUX_API_KEY = dOdEj91ZiMvnDMFVP9n2hwoz1rMTm7cy3OnjA0Xv

# ==========================
# 1. Charger modèles IA
# ==========================
@st.cache_resource
def load_models():
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    sentiment_analyzer = pipeline("sentiment-analysis")
    return summarizer, sentiment_analyzer

summarizer, sentiment_analyzer = load_models()

def analyze_text(text):
    # Résumé
    summary = summarizer(text, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
    # Sentiment
    sentiment = sentiment_analyzer(text)[0]
    sentiment_score = f"{sentiment['label']} ({round(sentiment['score']*100, 2)}%)"
    return summary, sentiment_score

# ==========================
# 2. Récupération des news
# ==========================
def get_news_finnhub():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    response = requests.get(url).json()
    news_list = []
    for n in response[:10]:
        news_list.append({
            "source": "Finnhub",
            "headline": n.get("headline"),
            "summary": n.get("summary"),
            "url": n.get("url"),
            "datetime": n.get("datetime")
        })
    return pd.DataFrame(news_list)

def get_news_marketaux():
    url = f"https://api.marketaux.com/v1/news/all?countries=us,fr,cn&api_token={MARKETAUX_API_KEY}"
    response = requests.get(url).json()
    news_list = []
    for n in response["data"][:10]:
        news_list.append({
            "source": "Marketaux",
            "headline": n.get("title"),
            "summary": n.get("description"),
            "url": n.get("url"),
            "datetime": n.get("published_at")
        })
    return pd.DataFrame(news_list)

# ==========================
# 3. Macro & Prévisions
# ==========================
def get_macro_indicators():
    url = f"https://api.tradingeconomics.com/indicators?c=guest:guest&f=json"
    response = requests.get(url).json()
    macro_list = []
    for i in response[:50]:
        macro_list.append({
            "country": i.get("Country"),
            "indicator": i.get("Category"),
            "latest_value": i.get("LatestValue"),
            "unit": i.get("Unit"),
            "forecast": i.get("Forecast")
        })
    return pd.DataFrame(macro_list)

# ==========================
# 4. Prévisions IA avec Prophet
# ==========================
def forecast_indicator(df, country, indicator):
    url = f"https://api.tradingeconomics.com/historical/country/{country}/indicator/{indicator}?c=guest:guest&f=json"
    data = requests.get(url).json()
    hist = pd.DataFrame(data)
    hist = hist[['DateTime', 'Value']].rename(columns={"DateTime": "ds", "Value": "y"})
    hist['ds'] = pd.to_datetime(hist['ds'])

    if len(hist) < 5:
        return None, None

    model = Prophet()
    model.fit(hist)
    future = model.make_future_dataframe(periods=12, freq='M')
    forecast = model.predict(future)
    return hist, forecast

# ==========================
# 5. Interface Streamlit
# ==========================
st.title("🌍 Dashboard Économie Mondiale - PRO (Gratuit)")
st.write("News + Indicateurs + Analyse IA + Graphiques + Prévisions")

# Récupération des données
with st.spinner("Chargement des données..."):
    news_df = pd.concat([get_news_finnhub(), get_news_marketaux()], ignore_index=True)
    macro_df = get_macro_indicators()

# --- FILTRES ---
st.sidebar.header("Filtres")
selected_country = st.sidebar.selectbox("Choisir un pays", sorted(macro_df['country'].dropna().unique()))
selected_indicator = st.sidebar.selectbox("Choisir un indicateur", sorted(macro_df['indicator'].dropna().unique()))

# ---------------- NEWS ----------------
st.subheader("📰 Dernières actualités économiques")
for index, row in news_df.iterrows():
    st.markdown(f"**{row['headline']}**")
    st.write(f"*{row['summary']}*")
    st.write(f"[Lien vers l'article]({row['url']})")
    
    if st.button(f"Analyser cette news", key=f"btn_{index}"):
        summary, sentiment = analyze_text(row['summary'])
        st.write(f"**Résumé IA :** {summary}")
        st.write(f"**Sentiment :** {sentiment}")

# ---------------- INDICATEURS MACRO ----------------
st.subheader(f"📊 Indicateurs Macro pour {selected_country}")
country_data = macro_df[macro_df['country'] == selected_country]
st.dataframe(country_data)

# ---------------- GRAPHIQUE ----------------
fig = px.bar(country_data, x="indicator", y="latest_value", color="indicator", title=f"Valeurs Macro - {selected_country}")
st.plotly_chart(fig)

# ---------------- PRÉVISION ----------------
st.subheader(f"📈 Prévisions IA pour {selected_indicator} ({selected_country})")
hist, forecast = forecast_indicator(macro_df, selected_country, selected_indicator)
if hist is not None:
    fig_forecast = px.line(forecast, x='ds', y='yhat', title=f"Prévision {selected_indicator} ({selected_country})")
    st.plotly_chart(fig_forecast)
else:
    st.warning("Pas assez de données pour prévoir cet indicateur.")
