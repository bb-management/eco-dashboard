import streamlit as st
import requests
import pandas as pd
from transformers import pipeline
import os

# --- CLÉS API ---
FINNHUB_API_KEY = "d1sua1pr01qhe5rc4vj0d1sua1pr01qhe5rc4vjg"
# Marketaux désactivé temporairement à cause de l'erreur 402

# --- Chargement des modèles IA avec cache ---
@st.cache_resource
def load_models():
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    sentiment_analyzer = pipeline("sentiment-analysis")
    # Traduction nécessite sentencepiece (installer en local)
    try:
        translator = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr")
    except Exception as e:
        st.warning("Impossible de charger le modèle de traduction. Assurez-vous d'avoir installé 'sentencepiece'.")
        translator = None
    return summarizer, sentiment_analyzer, translator

summarizer, sentiment_analyzer, translator = load_models()

# --- Fonctions récupération news ---

def get_news_finnhub():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        news = response.json()
        return news
    except Exception as e:
        st.error(f"Erreur lors de la récupération des news Finnhub : {e}")
        return []

# Marketaux désactivé temporairement pour éviter l’erreur 402
def get_news_marketaux():
    return []

# --- Filtrer les articles importants économie ---
def filter_important_news(news_list):
    keywords = ["economic", "finance", "market", "inflation", "gdp", "unemployment", "interest rate", "stock", "trade", "bank"]
    filtered = []
    for article in news_list:
        text = (article.get('headline') or "") + " " + (article.get('summary') or "") + " " + (article.get('category') or "")
        if any(kw.lower() in text.lower() for kw in keywords):
            filtered.append(article)
    return filtered

# --- Traduction ---
def translate_text(text):
    if translator is None:
        return text
    try:
        result = translator(text, max_length=512)
        return result[0]['translation_text']
    except Exception as e:
        return text

# --- Résumé et sentiment ---
def analyze_text(text):
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
    sentiment = sentiment_analyzer(text)[0]
    return summary, sentiment

# --- Streamlit app ---
st.title("🌍 Dashboard Économie Mondiale")
st.write("📰 Dernières actualités économiques")

news_finnhub = get_news_finnhub()
news_marketaux = get_news_marketaux()
all_news = news_finnhub + news_marketaux

important_news = filter_important_news(all_news)

for article in important_news[:10]:
    headline = article.get('headline') or article.get('title') or "Titre non disponible"
    summary = article.get('summary') or article.get('description') or ""
    url = article.get('url') or article.get('article_url') or ""

    # Traduction
    headline_fr = translate_text(headline)
    summary_fr = translate_text(summary)

    # Analyse IA sur résumé français
    ia_summary, sentiment = analyze_text(summary_fr)

    st.markdown(f"### {headline_fr}")
    st.markdown(f"[Lien vers l'article]({url})")
    st.markdown(f"**Résumé IA :** {ia_summary}")
    st.markdown(f"**Sentiment :** {sentiment['label']} ({sentiment['score']*100:.2f}%)")
    st.write("---")
