import streamlit as st
import requests
import pandas as pd
from transformers import pipeline

# Tes clés API — remplace par tes vraies clés
FINNHUB_API_KEY = "d1sua1pr01qhe5rc4vj0d1sua1pr01qhe5rc4vjg"
MARKETAUX_API_KEY = "dOdEj91ZiMvnDMFVP9n2hwoz1rMTm7cy3OnjA0Xv"

@st.cache_resource(show_spinner=False)
def load_models():
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    sentiment_analyzer = pipeline("sentiment-analysis")
    try:
        translator = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr", use_auth_token=False)
    except Exception as e:
        st.warning(f"Impossible de charger le modèle de traduction : {e}")
        translator = None
    return summarizer, sentiment_analyzer, translator

summarizer, sentiment_analyzer, translator = load_models()

def translate_text(text):
    if translator is None:
        return text
    try:
        if len(text) > 512:
            text = text[:512]
        result = translator(text)
        return result[0]['translation_text']
    except Exception as e:
        st.warning(f"Erreur de traduction : {e}")
        return text

def get_news_finnhub():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    # Filtrer uniquement les news avec mots-clés économiques (exemple simple)
    filtered = [item for item in data if any(k in item['headline'].lower() for k in ['économie', 'economic', 'marché', 'finance', 'bourse', 'inflation'])]
    return filtered[:10]

def get_news_marketaux():
    url = f"https://api.marketaux.com/v1/news/all?api_token={MARKETAUX_API_KEY}&language=en"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    filtered = [item for item in data['data'] if any(k in item['title'].lower() for k in ['economy', 'market', 'finance', 'inflation', 'stock'])]
    return filtered[:10]

def analyze_and_translate_articles(articles):
    results = []
    for art in articles:
        title = art.get('headline') or art.get('title') or ''
        summary = art.get('summary') or ''
        url = art.get('url') or art.get('source_url') or ''
        
        # Résumé IA
        summary_ai = summarizer(summary or title, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        summary_fr = translate_text(summary_ai)
        
        # Analyse sentiment
        sentiment = sentiment_analyzer(summary_ai)[0]
        
        results.append({
            'title': translate_text(title),
            'summary': summary_fr,
            'sentiment': f"{sentiment['label']} ({sentime
