import streamlit as st
import requests
import pandas as pd
from transformers import pipeline
import time

# Tes clés API — à remplacer par tes vraies clés
FINNHUB_API_KEY = "d1sua1pr01qhe5rc4vj0d1sua1pr01qhe5rc4vjg"
MARKETAUX_API_KEY = "dOdEj91ZiMvnDMFVP9n2hwoz1rMTm7cy3OnjA0Xv"

# Liste de mots clés pour filtrer les articles économiques
KEYWORDS_ECO = [
    "économie", "marché", "inflation", "banque", "investissement", "bourse",
    "croissance", "emploi", "taux", "finance", "industrie", "PIB", "chômage",
    "récession", "export", "import", "dette", "trésor", "action", "dividende"
]

# Chargement des modèles avec cache pour ne pas recharger à chaque fois
@st.cache_resource(show_spinner=False)
def load_models():
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    sentiment_analyzer = pipeline("sentiment-analysis")
    translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
    return summarizer, sentiment_analyzer, translator

summarizer, sentiment_analyzer, translator = load_models()

def translate_text(text):
    # Limiter la longueur sinon erreur max_length
    if len(text) > 512:
        text = text[:512]
    result = translator(text)
    return result[0]['translation_text']

def get_news_finnhub():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Erreur lors de la récupération des news Finnhub")
        return []
    news = response.json()
    return news

def get_news_marketaux():
    url = f"https://api.marketaux.com/v1/news/all?api_token={MARKETAUX_API_KEY}&language=en"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Erreur lors de la récupération des news Marketaux")
        return []
    data = response.json()
    return data.get("data", [])

def filter_economic_news(news_list):
    filtered = []
    for news in news_list:
        # Chercher mots clés dans titre ou description (en minuscule)
        title = news.get("headline") or news.get("title") or ""
        description = news.get("summary") or news.get("description") or ""
        text_to_check = (title + " " + description).lower()
        if any(keyword in text_to_check for keyword in KEYWORDS_ECO):
            filtered.append(news)
    return filtered

def analyze_sentiment(text):
    # Le pipeline renvoie une liste [{'label':..., 'score':...}]
    results = sentiment_analyzer(text)
    labels = {"POSITIVE": "POSITIVE", "NEGATIVE": "NEGATIVE", "NEUTRAL": "NEUTRE"}
    label = results[0]["label"]
    score = results[0]["score"] * 100
    return labels.get(label, label), score

def main():
    st.title("🌍 Dashboard Économie Mondiale - PRO (Gratuit)")
    st.markdown("News + Indicateurs + Analyse IA + Graphiques + Prévisions")

    with st.spinner("Récupération des actualités..."):
        news_finnhub = get_news_finnhub()
        news_marketaux = get_news_marketaux()

    news_all = news_finnhub + news_marketaux
    news_filtered = filter_economic_news(news_all)

    st.header("📰 Dernières actualités économiques filtrées")

    if not news_filtered:
        st.info("Aucune actualité économique récente trouvée.")
        return

    for news in news_filtered[:10]:  # limite à 10 articles
        title_en = news.get("headline") or news.get("title") or "Sans titre"
        url = news.get("url") or news.get("link") or "#"
        description_en = news.get("summary") or news.get("description") or ""

        # Traduction titre et description
        title_fr = translate_text(title_en)
        description_fr = translate_text(description_en) if description_en else ""

        # Résumé IA (en anglais avant traduction)
        summary_en = summarizer(description_en, max_length=130, min_length=30, do_sample=False)[0]["summary_text"] if description_en else "Résumé non disponible"
        summary_fr = translate_text(summary_en)

        # Analyse sentiment sur résumé anglais (plus fiable en anglais)
        sentiment_label, sentiment_score = analyze_sentiment(summary_en)

        # Affichage
        st.markdown(f"### [{title_fr}]({url})")
        st.markdown(f"**Résumé IA :** {summary_fr}")
        st.markdown(f"**Sentiment :** {sentiment_label} ({sentiment_score:.2f}%)")
        st.markdown("---")

        # Petit délai pour éviter surcharge API modèles locaux
        time.sleep(0.5)

if __name__ == "__main__":
    main()
