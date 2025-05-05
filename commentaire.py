import requests
from bs4 import BeautifulSoup
import logging
import json
import re

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_amazon_product_info(url):
    """Scrape les informations du produit et les avis de la page produit Amazon."""
    logger.info("Début du scraping des informations produit")
    
    # En-têtes pour simuler un navigateur
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        # Requête HTTP
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Connexion réussie: code {response.status_code}")
            
            # Parser le HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraire le titre du produit
            product_title_element = soup.find('span', id='productTitle')
            title = product_title_element.text.strip() if product_title_element else "Titre inconnu"
            
            # Extraire l'ASIN (identifiant produit)
            asin = extract_asin_from_url(url)
            
            # Construire le lien vers la page des avis
            reviews_link = f"https://www.amazon.co.uk/product-reviews/{asin}" if asin else None
            
            # Extraire les avis de la page actuelle
            reviews = extract_reviews_from_page(soup)
            
            # Résultats
            product_info = {
                'title': title,
                'asin': asin,
                'reviews_link': reviews_link,
                'reviews': reviews
            }
            
            logger.info(f"Scraping produit terminé: {len(reviews)} avis extraits")
            return product_info
        
        else:
            logger.error(f"Échec de la connexion: code {response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return None

def extract_asin_from_url(url):
    """Extraire l'ASIN du produit à partir de l'URL."""
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if asin_match:
        return asin_match.group(1)
    return None

def extract_reviews_from_page(soup):
    """Extraire les avis de la page actuelle au format spécifié."""
    logger.info("Extraction des avis")
    reviews = []
    
    # Rechercher les blocs d'avis
    review_elements = soup.find_all('div', {'data-hook': 'review'}) or \
                     soup.find_all('div', {'id': lambda x: x and x.endswith('-review-card')})
    
    logger.info(f"Nombre d'avis trouvés: {len(review_elements)}")
    
    for review_element in review_elements:
        try:
            # Initialiser un dictionnaire pour stocker les informations de l'avis
            review_data = {}
            
            # 1. Nom du reviewer
            profile_element = review_element.find('a', class_='a-profile')
            if profile_element:
                name_element = profile_element.find('span', class_='a-profile-name')
                review_data['reviewer'] = name_element.text.strip() if name_element else "Anonyme"
            else:
                review_data['reviewer'] = "Anonyme"
            
            # 2. Note (étoiles)
            rating_element = review_element.find('i', {'data-hook': 'review-star-rating'})
            if rating_element:
                rating_text = rating_element.find('span', class_='a-icon-alt')
                if rating_text:
                    # Extraire le nombre (ex: "5.0 out of 5 stars" -> 5)
                    rating_match = re.search(r'(\d+\.\d+|\d+)', rating_text.text)
                    review_data['rating'] = float(rating_match.group(1)) if rating_match else 0
                else:
                    # Méthode alternative basée sur les classes
                    star_class = None
                    for cls in rating_element.get('class', []):
                        if cls.startswith('a-star-'):
                            star_class = cls
                            break
                    if star_class:
                        review_data['rating'] = float(star_class.replace('a-star-', ''))
                    else:
                        review_data['rating'] = 0
            else:
                review_data['rating'] = 0
            
            # 3. Titre de l'avis
            title_element = review_element.find('a', {'data-hook': 'review-title'})
            if title_element:
                # Trouver le texte dans les spans
                title_spans = title_element.find_all('span')
                if title_spans:
                    # Prendre le dernier span qui contient généralement le titre
                    review_data['title'] = title_spans[-1].text.strip()
                else:
                    # Si pas de spans, prendre tout le texte
                    review_data['title'] = title_element.text.strip()
            else:
                review_data['title'] = "Sans titre"
            
            # 4. Date et lieu de l'avis - MODIFIÉ
            date_element = review_element.find('span', {'data-hook': 'review-date'})
            if date_element:
                full_date_text = date_element.text.strip()
                # Extraire le lieu et la date avec regex
                location_date_pattern = r'Reviewed in (.*?) on (.*)'
                match = re.search(location_date_pattern, full_date_text)
                
                if match:
                    review_data['location'] = match.group(1)
                    review_data['date'] = match.group(2)
                else:
                    # Si le pattern ne correspond pas, garder la chaîne complète dans date
                    review_data['location'] = "Unknown"
                    review_data['date'] = full_date_text
            else:
                review_data['location'] = "Unknown"
                review_data['date'] = "Date inconnue"
            
            # 5. Achat vérifié
            verified_element = review_element.find('span', {'data-hook': 'avp-badge'})
            review_data['verified_purchase'] = True if verified_element else False
            
            # 6. Contenu de l'avis
            # MODIFICATION: Extraction du texte nettoyé de l'avis
            review_body_element = review_element.find('span', {'data-hook': 'review-body'})
            
            if review_body_element:
                # Trouver le contenu réel du texte
                # Chercher d'abord dans la div avec la classe reviewText
                review_text_div = review_body_element.find('div', class_='reviewText')
                
                if review_text_div:
                    # Trouver le span contenant le texte
                    span_content = review_text_div.find('span')
                    if span_content:
                        # Extraire uniquement le texte, sans balises HTML
                        review_data['_comment'] = span_content.get_text(strip=True)
                    else:
                        review_data['_comment'] = review_text_div.get_text(strip=True)
                else:
                    # Chercher directement tous les spans contenus dans l'élément review-body
                    spans = review_body_element.find_all('span')
                    # Prendre le contenu textuel du dernier span qui contient généralement le texte principal
                    if spans:
                        for span in spans:
                            # Si le span a du contenu textuel, c'est probablement le bon
                            if span.get_text(strip=True):
                                review_data['_comment'] = span.get_text(strip=True)
                                break
                        else:  # Si aucun span n'a été trouvé avec du contenu
                            review_data['_comment'] = review_body_element.get_text(strip=True)
                    else:
                        review_data['_comment'] = review_body_element.get_text(strip=True)
            else:
                review_data['_comment'] = "Aucun commentaire disponible"
            
            # 7. Nombre de personnes qui ont trouvé cet avis utile
            helpful_element = review_element.find('span', {'data-hook': 'helpful-vote-statement'})
            helpful_count = 0
            if helpful_element:
                helpful_match = re.search(r'(\d+)', helpful_element.text)
                helpful_count = int(helpful_match.group(1)) if helpful_match else 0
            
            # Ajouter cette information aux données de l'avis
            review_data['helpful_count'] = helpful_count
            
            # 8. NOUVEAU: Extraire les images associées à l'avis
            review_data['images'] = []
            
            # Rechercher les sections d'images
            # Méthode 1: Rechercher par l'ID qui contient "imageSection"
            image_sections = review_element.find_all('div', id=lambda x: x and 'imageSection' in x)
            
            # Méthode 2: Rechercher par classe "review-image-container"
            if not image_sections:
                image_sections = review_element.find_all('div', class_='review-image-container')
            
            # Méthode 3: Rechercher directement les balises img dans le corps de l'avis
            if not image_sections:
                image_sections = [review_element]  # Utiliser tout l'élément d'avis pour chercher des images
            
            # Parcourir toutes les sections d'images trouvées
            for section in image_sections:
                # Trouver toutes les balises img
                img_tags = section.find_all('img', class_='review-image-tile')
                
                # Si aucune image n'est trouvée avec la classe spécifique, chercher toutes les images
                if not img_tags:
                    img_tags = section.find_all('img', alt='Customer image')
                
                # Si toujours rien, chercher toutes les images
                if not img_tags:
                    img_tags = section.find_all('img')
                
                # Extraire les URLs des images
                for img in img_tags:
                    if img.get('src'):
                        img_url = img['src'].strip()
                        # Ne pas ajouter d'URLs vides ou de placeholders
                        if img_url and not img_url.endswith('placeholder.png') and not img_url.endswith('transparent-pixel.gif'):
                            # Améliorer la qualité de l'image en remplaçant les suffixes de taille
                            # Ex: _SY88.jpg -> .jpg pour obtenir l'image en pleine résolution
                            img_url = re.sub(r'_(SY|SX|UL|UR|UC|AC|SR)\d+\.(jpg|png|gif)', r'.\2', img_url)
                            review_data['images'].append(img_url)
            
            reviews.append(review_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'un avis: {e}")
    
    return reviews

def save_to_json(data, filename):
    """Sauvegarder les données dans un fichier JSON."""
    logger.info(f"Sauvegarde dans {filename}")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Données sauvegardées dans {filename}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        return False

def main():
    """Fonction principale d'exécution."""
    # URL du produit à scraper
    url = "https://www.amazon.co.uk/Lenovo-IdeaPad-Chromebook-Laptop-Celeron/dp/B0DNK1WFV6/ref=sr_1_6"
    
    # Scraper les informations du produit et les avis de la page produit
    product_info = scrape_amazon_product_info(url)
    
    if not product_info:
        logger.error("Échec du scraping. Arrêt.")
        return
    
    # Sauvegarder les résultats
    if save_to_json(product_info, 'amazon_reviews.json'):
        logger.info("Scraping terminé avec succès!")
        
        # Afficher un exemple du premier avis
        if product_info.get('reviews'):
            logger.info(f"Exemple du premier avis extrait: {json.dumps(product_info['reviews'][0], indent=2, ensure_ascii=False)}")
    else:
        logger.error("Erreur lors de la sauvegarde des résultats.")

if __name__ == "__main__":
    main()