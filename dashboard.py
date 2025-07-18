import streamlit as st
import requests
import plotly.graph_objects as go

# ---------------------
# CONFIGURATION
# ---------------------
FINNHUB_API_KEY = "d1sua1pr01qhe5rc4vj0d1sua1pr01qhe5rc4vjg"
MARKETAUX_API_KEY = "dOdEj91ZiMvnDMFVP9n2hwoz1rMTm7cy3OnjA0Xv"

FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"
FINNHUB_QUOTE_URL = "https://finnhub.io/api/v1/quote"
FINNHUB_INDEXES = {
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "CAC 40": "^FCHI",
    "DAX": "^GDAXI"
}

# ---------------------
# TRADUCTION
# ---------------------
def translate_text(text, source_lang="en", target_lang="fr"):
    try:
        url = "https://libretranslate.com/translate"
        payload = {"q": text, "source": source_lang, "target": target_lang, "format": "text"}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json().get("translatedText", text)
    except:
        return text

# ---------------------
# API HUGGINGFACE INFERENCE
# ---------------------
def summarize_text(text):
    api_url = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {"Authorization": "Bearer hf_YOUR_HF_API_KEY"}  # remplace par ta clé HuggingFace
    payload = {"inputs": text}
    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()[0]['summary_text']

def analyze_sentiment(text):
    api_url = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
    headers = {"Authorization": "Bearer hf_YOUR_HF_API_KEY"}
    payload = {"inputs": text}
    response = requests.post(api_url, headers=headers, json=payload)
    return response.json()[0]

# ---------------------
# ACTUALITÉS & QUOTES
# ---------------------
def get_finnhub_news():
    try:
        response = requests.get(FINNHUB_NEWS_URL, params={"category": "general", "token": FINNHUB_API_KEY})
        return response.json()
    except:
        return []

def get_index_price(symbol):
    try:
        response = requests.get(FINNHUB_QUOTE_URL, params={"symbol": symbol, "token": FINNHUB_API_KEY})
        return response.json().get("c", None)
    except:
        return None

# ---------------------
# INTERFACE STREAMLIT
# ---------------------
st.set_page_config(page_title="🌍 Dashboard Économie Mondiale", layout="wide")
st.title("🌍 Dashboard Économie Mondiale - Version Cloud")

# ---------------------
# SECTION 1 : INDICES MONDIAUX
# ---------------------
st.header("📊 Indices Boursiers Mondiaux")
cols = st.columns(len(FINNHUB_INDEXES))
for i, (name, symbol) in enumerate(FINNHUB_INDEXES.items()):
    price = get_index_price(symbol)
    if price:
        cols[i].metric(label=name, value=f"{price:.2f} $")
    else:
        cols[i].write("Erreur")

# ---------------------
# SECTION 2 : ACTUALITÉS
# ---------------------
st.header("📰 Dernières actualités économiques")
news = get_finnhub_news()
if isinstance(news, list) and len(news) > 0:
    for article in news[:5]:
        title = article.get("headline", "Sans titre")
        summary = article.get("summary", "")
        url = article.get("url", "#")
        translated_title = translate_text(title)
        translated_summary = translate_text(summary)
        st.subheader(f"🔹 {translated_title}")
        st.write(translated_summary)
        st.markdown(f"[Lire l'article complet]({url})")
else:
    st.warning("Impossible de récupérer les actualités.")

# ---------------------
# SECTION 3 : ANALYSE
# ---------------------
st.header("🧠 Analyse de texte économique")
input_text = st.text_area("Colle un article ou un paragraphe en anglais :")

if st.button("Analyser"):
    if input_text.strip():
        with st.spinner("Analyse en cours..."):
            summary = summarize_text(input_text)
            sentiment = analyze_sentiment(summary)
            translated_summary = translate_text(summary)
        st.subheader("Résumé (EN) :")
        st.write(summary)
        st.subheader("Résumé traduit (FR) :")
        st.write(translated_summary)
        st.subheader("Sentiment :")
        st.write(f"{sentiment['label']} (score : {round(sentiment['score'], 2)})")
    else:
        st.warning("Veuillez entrer un texte.")
