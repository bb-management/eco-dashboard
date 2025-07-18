import streamlit as st
import requests
import plotly.graph_objects as go
from transformers import pipeline

# ---------------------
# CONFIGURATION
# ---------------------
# --- 2. Clés API (exemple) ---
FINNHUB_API_KEY = "d1sua1pr01qhe5rc4vj0d1sua1pr01qhe5rc4vjg"
MARKETAUX_API_KEY = "dOdEj91ZiMvnDMFVP9n2hwoz1rMTm7cy3OnjA0Xv"
DEEPL_API_KEY = "ta_cle_deepl_ici"  # Remplace par ta vraie clé DeepL

# --- 3. Fonctions pour récupérer les news ---
def get_news_finnhub():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    articles = response.json()
    return articles

def get_news_marketaux():
    url = f"https://api.marketaux.com/v1/news/all?api_token={MARKETAUX_API_KEY}&language=en"
    response = requests.get(url)
    data = response.json()
    return data.get('data', [])

# --- 4. Filtrage des articles importants économiquement ---
keywords = ['inflation', 'growth', 'stock market', 'central bank', 'gdp', 'economy', 'finance', 'interest rate', 'recession']

def filter_articles(articles):
    filtered = []
    for article in articles:
        title = article.get('headline') or article.get('title') or ''
        summary = article.get('summary') or article.get('description') or ''
        text = (title + ' ' + summary).lower()
        if any(keyword in text for keyword in keywords):
            filtered.append(article)
    return filtered
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
# CHARGEMENT DES MODELS
# ---------------------
@st.cache_resource
def load_models():
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return summarizer, sentiment_analyzer

summarizer, sentiment_analyzer = load_models()

# ---------------------
# TRADUCTION LIBRETRANSLATE
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
# ACTUALITÉS ÉCONOMIQUES (FINNHUB)
# ---------------------
def get_finnhub_news():
    try:
        params = {"category": "general", "token": FINNHUB_API_KEY}
        response = requests.get(FINNHUB_NEWS_URL, params=params)
        return response.json()
    except:
        return []

# ---------------------
# QUOTES INDICES (FINNHUB)
# ---------------------
def get_index_price(symbol):
    try:
        params = {"symbol": symbol, "token": FINNHUB_API_KEY}
        response = requests.get(FINNHUB_QUOTE_URL, params=params).json()
        return response.get("c", None)
    except:
        return None

# ---------------------
# INTERFACE STREAMLIT
# ---------------------
st.set_page_config(page_title="🌍 Dashboard Économie Mondiale", layout="wide")
st.title("🌍 Dashboard Économie Mondiale - Version PRO")

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
    for article in news[:5]:  # Limite à 5 articles
        title = article.get("headline", "Sans titre")
        summary = article.get("summary", "")
        url = article.get("url", "#")

        translated_title = translate_text(title)
        translated_summary = translate_text(summary)

        st.subheader(f"🔹 {translated_title}")
        st.write(translated_summary)
        st.markdown(f"[Lire l'article complet]({url})")
else:
    st.warning("Impossible de récupérer les actualités. Vérifie ta clé Finnhub.")

# ---------------------
# SECTION 3 : ANALYSE DE TEXTE
# ---------------------
st.header("🧠 Analyse de texte économique")
input_text = st.text_area("Colle un article ou un paragraphe en anglais :")

if st.button("Analyser"):
    if input_text.strip():
        with st.spinner("Analyse en cours..."):
            summary = summarizer(input_text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
            sentiment = sentiment_analyzer(summary)[0]
            translated_summary = translate_text(summary)

        st.subheader("Résumé (EN) :")
        st.write(summary)

        st.subheader("Résumé traduit (FR) :")
        st.write(translated_summary)

        st.subheader("Sentiment :")
        st.write(f"{sentiment['label']} (score : {round(sentiment['score'], 2)})")
    else:
        st.warning("Veuillez entrer un texte avant d'analyser.")
