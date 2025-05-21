import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import spacy
from collections import Counter

# 1. Charger les données
df = pd.read_excel("amazon_reviews_cleaned.xlsx")

# 2. Vérifier la colonne de texte
if 'comment' not in df.columns:
    raise ValueError("La colonne 'comment' est manquante dans le fichier.")

# 3. Charger le modèle NLP français
nlp = spacy.load("fr_core_news_sm")
nlp.max_length = 2_000_000

# 4. Traiter les commentaires
comments = df['comment'].dropna()
docs = [nlp(str(comment)) for comment in comments if isinstance(comment, str)]

# 5. Extraire les lemmes utiles
tokens = [
    token.lemma_.lower()
    for doc in docs
    for token in doc
    if token.is_alpha and not token.is_stop and token.pos_ in ['NOUN', 'ADJ', 'VERB']
]

# 6. Compter les fréquences
freq = Counter(tokens)
most_common_text = " ".join([word for word, count in freq.most_common(200)])

# 7. Générer le WordCloud sans fond
wordcloud = WordCloud(
    width=1000,
    height=600,
    background_color=None,  # Pas de fond
    mode='RGBA',            # Format avec canal alpha (transparence)
    max_words=200,
    max_font_size=120,
    random_state=42,
    colormap='Pastel1'
).generate(most_common_text)

# 8. Afficher et enregistrer (transparent)
plt.figure(figsize=(12, 7))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.tight_layout(pad=0)

# Sauvegarde avec transparence
plt.savefig(
    r"C:\Users\Dell\Desktop\BD&IA 4\analyse du web\projet_reviews_amazon\images\wordcloud.png",
    format='png',
    transparent=True
)
plt.close()
