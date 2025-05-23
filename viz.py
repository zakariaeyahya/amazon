import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import nltk
import re
from nltk.corpus import stopwords
import spacy
from collections import Counter

# Téléchargement des stopwords NLTK
nltk.download('stopwords')

# --- Configuration de la page ---
st.set_page_config(
    page_title="Analyse Produits Amazon",
    page_icon=r"images\amazon_logo1.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Chemins des fichiers locaux ---
CHEMIN_LOGO = r"images/amazon_logo.png"
CHEMIN_BANNIERE = r"images\image.jpg"
CHEMIN_LOGO_SIDEBAR = r"images/logo.png"
CHEMIN_DATA = r"fulldataa.csv"
CHEMIN_SENTIMENTS = r"sentiments_par_asin.csv"

# --- Affichage Logo & Titre ---
st.image(CHEMIN_BANNIERE, use_column_width=True)
st.title("💻 Analyse des Avis Amazon : Laptops")
st.markdown("Bienvenue dans l'analyse des produits Amazon ! Filtrez, explorez et découvrez des insights sur les ordinateurs portables à partir des avis clients.")

# --- Chargement des données avec cache ---
@st.cache_data
def load_data():
    df = pd.read_csv(CHEMIN_DATA)
    df["PRIX"] = df["PRIX"].str.replace("£", "").str.replace(",", "").astype(float)
    df.dropna(subset=["PRIX", "NOTE"], inplace=True)
    df["CLASSE"] = df["CLASSE"].astype(str)

    sentiments = pd.read_csv(CHEMIN_SENTIMENTS)
    if "ASIN" in df.columns and "asin" in sentiments.columns:
        sentiments.rename(columns={"asin": "ASIN"}, inplace=True)
        df = df.merge(sentiments, on="ASIN", how="left")
    df['sentiment'] = df['sentiment'].fillna('Neutral')
    return df, sentiments

df, sentiments = load_data()

# --- Barre latérale ---
st.sidebar.image(CHEMIN_LOGO_SIDEBAR, use_column_width=True ,width=80)

st.sidebar.markdown("""
Plongez au cœur des avis Amazon pour laptops !  
Filtrez, comparez et dénichez les meilleures perles tech en un clic.
""")
st.sidebar.title("📂 Menu")
page = st.sidebar.radio("Navigation", ["📊 Visualisation des données", "🛒 Recommandation de produits"])

# ================================
# PAGE 1 : Visualisation des données
# ================================
if page == "📊 Visualisation des données":
    st.header("📊 Visualisation des Données Produits")

    with st.expander("🔎 Affiner la sélection des produits", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fabricants = st.multiselect("Fabricants", sorted(df["MANUFACTURER"].dropna().unique()))
        with col2:
            classes = st.multiselect("Classes", sorted(df["CLASSE"].dropna().unique()))
        with col3:
            prix_range = st.slider("Prix (£)", float(df["PRIX"].min()), float(df["PRIX"].max()),
                                   (float(df["PRIX"].min()), float(df["PRIX"].max())))
        with col4:
            note_min = st.slider("Note minimale", 0.0, 5.0, 3.0, 0.1)

    df_filtered = df[(df["PRIX"] >= prix_range[0]) & (df["PRIX"] <= prix_range[1]) & (df["NOTE"] >= note_min)]
    if fabricants:
        df_filtered = df_filtered[df_filtered["MANUFACTURER"].isin(fabricants)]
    if classes:
        df_filtered = df_filtered[df_filtered["CLASSE"].isin(classes)]

    st.markdown("### 📈 Graphiques Amazon Style")
    col1, col2 = st.columns(2)

    with col1:
        note_moy = df_filtered.groupby("MANUFACTURER")["NOTE"].mean().sort_values(ascending=False).head(10).reset_index()
        fig1 = px.bar(note_moy, x="NOTE", y="MANUFACTURER", orientation="h", color="NOTE",
                      color_continuous_scale=["#FF9900", "#232F3E"],
                      title="🔝 Top Fabricants par Note Moyenne")
        st.plotly_chart(fig1, use_container_width=True)

        prix_classe = df_filtered.groupby("CLASSE")["PRIX"].mean().reset_index()
        fig2 = px.bar(prix_classe, x="CLASSE", y="PRIX", color="PRIX",
                      color_continuous_scale=["#FF9900", "#232F3E"],
                      title="💰 Prix Moyen par Classe")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.histogram(df_filtered, x="NOTE", nbins=20, title="⭐ Distribution des Notes",
                            color_discrete_sequence=["#FF9900"])
        st.plotly_chart(fig3, use_container_width=True)

        sentiment_counts = df_filtered['sentiment'].value_counts().reset_index()
        sentiment_counts.columns = ["Sentiment", "Count"]
        fig4 = px.pie(sentiment_counts, names='Sentiment', values='Count', title="🗣 Répartition des Sentiments",
                      color='Sentiment', color_discrete_map={
                          "Positive": "#D5DBDB",
                          "Neutral": "#FF9900",
                          "Negative": "#232F3E"
                      })
        st.plotly_chart(fig4, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        counts_classe = df_filtered["CLASSE"].value_counts().reset_index()
        counts_classe.columns = ["Classe", "Nombre de produits"]
        fig5 = px.bar(counts_classe, x="Classe", y="Nombre de produits",
                      title="📦 Nombre de Produits par Classe",
                      color_discrete_sequence=["#232F3E"])
        st.plotly_chart(fig5, use_container_width=True)

    with col4:
        fig6 = px.histogram(df_filtered, x="PRIX", nbins=30, title="💸 Distribution des Prix (£)",
                            color_discrete_sequence=["#FF9900"])
        st.plotly_chart(fig6, use_container_width=True)
# --- WordCloud NLP remplacé par une image ---
st.markdown("### ☁ Nuage de Mots basé sur l'Analyse NLP")
with st.expander("📝 Afficher le WordCloud NLP", expanded=True):
 
    chemin_image_wordcloud = r"C:\Users\Dell\Desktop\BD&IA 4\analyse du web\projet_reviews_amazon\images\wordcloud.png"  # <-- Chemin de votre image
    st.image(chemin_image_wordcloud, use_column_width=True)


# ================================
# PAGE 2 : Recommandation de Produits
# ================================
if page == "🛒 Recommandation de produits":
    st.header("🛒 Recommandation de Produits Amazon")
    prix_min, prix_max = float(df["PRIX"].min()), float(df["PRIX"].max())

    with st.form("reco_form"):
        col1, col2 = st.columns(2)

        with col1:
            budget_min = st.number_input("💰 Budget minimum (£)", min_value=prix_min, value=prix_min, step=10.0)
            budget_max = st.number_input("💰 Budget maximum (£)", min_value=budget_min, value=prix_max, step=10.0)
            note_min = st.slider("⭐ Note minimale", 0.0, 5.0, 4.0, 0.1)

        with col2:
            fabricants = st.multiselect("🏷 Marques", sorted(df["MANUFACTURER"].dropna().unique()))
            st.markdown("#### 🧠 RAM")
            ram_mode = st.radio("Mode de filtrage", ["Intervalle", "Exacte"], horizontal=True)
            if ram_mode == "Intervalle":
                ram_min = st.number_input("RAM min (Go)", min_value=0, value=4, step=1)
                ram_max = st.number_input("RAM max (Go)", min_value=ram_min, value=64, step=1)
            else:
                ram_exacte = st.number_input("RAM exacte (Go)", min_value=0, value=8, step=1)

        submitted = st.form_submit_button("🔍 Rechercher")

    if submitted:
        df_reco = df[
            (df["PRIX"] >= budget_min) &
            (df["PRIX"] <= budget_max) &
            (df["NOTE"] >= note_min)
        ]

        if fabricants:
            df_reco = df_reco[df_reco["MANUFACTURER"].isin(fabricants)]

        if "RAM" in df_reco.columns:
            df_reco["RAM"] = pd.to_numeric(df_reco["RAM"], errors="coerce")
            if ram_mode == "Intervalle":
                df_reco = df_reco[(df_reco["RAM"] >= ram_min) & (df_reco["RAM"] <= ram_max)]
            else:
                df_reco = df_reco[df_reco["RAM"] == ram_exacte]

        df_reco = df_reco.sort_values(by=["NOTE", "PRIX"], ascending=[False, True])

        st.subheader("✅ Produits recommandés")
        if df_reco.empty:
            st.warning("Aucun produit ne correspond à vos critères.")
        else:
            def lien_html(url, titre):
                return f'<a href="{url}" target="_blank">{titre}</a>' if pd.notna(url) and url.strip() else titre

            df_display = df_reco[["TITRE", "PRIX", "NOTE", "MANUFACTURER", "URL_INFO1"]].copy()
            df_display["TITRE"] = df_display.apply(lambda row: lien_html(row["URL_INFO1"], row["TITRE"]), axis=1)
            df_display.drop(columns=["URL_INFO1"], inplace=True)

            st.write(f"### 🔍 {len(df_display)} produit(s) recommandé(s)")
            st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)