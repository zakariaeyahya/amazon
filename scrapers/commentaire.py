import logging
import json
import re
import time
import csv
import os
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fichiers de données
PRODUCTS_CSV = "data/amazon_products_all.csv"
OUTPUT_CSV = "data/amazon_reviews_all.csv"
PROGRESS_FILE = "data/scraping_progress.json"

def setup_driver():
    """Configure et retourne une instance du WebDriver Firefox."""
    logger.info("Configuration du WebDriver Firefox")
    
    options = Options()
    # Options recommandées pour éviter la détection
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    
    # Définir un User-Agent réaliste
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0")
    
    # Décommentez pour exécuter en mode headless (sans interface graphique)
    # options.add_argument("--headless")
    
    try:
        # Version simple sans geckodriver spécifique
        driver = webdriver.Firefox(options=options)
        logger.info("Firefox WebDriver initialisé avec succès")
        return driver
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de Firefox WebDriver: {e}")
        
        logger.error("\n=== INSTRUCTIONS DE DÉPANNAGE ===")
        logger.error("1. Assurez-vous que Firefox est correctement installé")
        logger.error("2. Téléchargez manuellement geckodriver depuis:")
        logger.error("   https://github.com/mozilla/geckodriver/releases")
        logger.error("3. Placez geckodriver.exe dans le même dossier que ce script ou dans votre PATH")
        
        raise

def load_already_scraped_reviews():
    """Charge les commentaires déjà scrapés pour éviter les duplicats."""
    already_scraped = {}
    
    # Vérifier si le fichier de sortie existe
    if os.path.exists(OUTPUT_CSV):
        try:
            # Chargement des avis déjà scrapés
            df = pd.read_csv(OUTPUT_CSV)
            # Créer un dictionnaire avec asin et reviewer comme clés
            for _, row in df.iterrows():
                asin = row.get('asin', '')
                reviewer = row.get('reviewer', '')
                if asin not in already_scraped:
                    already_scraped[asin] = set()
                already_scraped[asin].add(reviewer)
            
            logger.info(f"Chargé {len(already_scraped)} produits avec des avis déjà scrapés")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des avis existants: {e}")
    
    return already_scraped

def load_progress():
    """Charge la progression du scraping pour reprendre où on s'était arrêté."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier de progression: {e}")
    
    return {"last_index": -1}

def save_progress(index):
    """Sauvegarde la progression du scraping."""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({"last_index": index}, f)
        logger.info(f"Progression sauvegardée: index {index}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la progression: {e}")

def scrape_amazon_product_info(url, asin, title, already_scraped_reviewers=None):
    """Scrape les informations du produit et les avis de la page produit Amazon avec Selenium."""
    if already_scraped_reviewers is None:
        already_scraped_reviewers = set()
        
    logger.info(f"Début du scraping pour le produit: {title} (ASIN: {asin})")
    
    driver = setup_driver()
    
    try:
        # Naviguer vers l'URL
        logger.info(f"Navigation vers {url}")
        driver.get(url)
        
        # Attendre que la page se charge complètement
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Vérifier et gérer les CAPTCHAs
        if not handle_captcha(driver):
            return []
            
        logger.info("Page chargée avec succès")
        
        # Extraire les avis de la page actuelle
        reviews = extract_reviews_from_page(driver, asin, already_scraped_reviewers)
        
        logger.info(f"Scraping produit terminé: {len(reviews)} nouveaux avis extraits")
        return reviews
    
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return []
    
    finally:
        # Fermer le navigateur
        logger.info("Fermeture du navigateur")
        driver.quit()

def extract_asin_from_url(url):
    """Extraire l'ASIN du produit à partir de l'URL."""
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if asin_match:
        return asin_match.group(1)
    return None

def extract_reviews_from_page(driver, asin, already_scraped_reviewers):
    """Extraire les avis de la page actuelle au format spécifié."""
    logger.info("Extraction des avis")
    reviews = []
    
    # Attendre que les avis se chargent
    try:
        # Vérifier s'il y a une section d'avis sur la page
        WebDriverWait(driver, 5).until(
            lambda d: d.find_elements(By.ID, "cm-cr-dp-recent-reviews") or 
                     d.find_elements(By.CSS_SELECTOR, 'div[data-hook="review"]')
        )
    except:
        logger.info("Pas de section d'avis trouvée, il pourrait ne pas y avoir d'avis sur cette page")
    
    # Trouver tous les blocs d'avis
    try:
        # Attendre un court instant pour s'assurer que tout est chargé
        time.sleep(2)
        
        # Rechercher les blocs d'avis avec différents sélecteurs possibles
        review_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-hook="review"]')
        
        if not review_elements:
            # Essayer un autre sélecteur si le premier ne fonctionne pas
            review_elements = driver.find_elements(By.CSS_SELECTOR, 'div[id$="-review-card"]')
        
        logger.info(f"Nombre d'avis trouvés sur la page: {len(review_elements)}")
        
        for review_element in review_elements:
            try:
                # Extraire le nom du reviewer d'abord pour vérifier s'il est déjà scrapé
                try:
                    profile_element = review_element.find_element(By.CSS_SELECTOR, 'a.a-profile')
                    name_element = profile_element.find_element(By.CSS_SELECTOR, 'span.a-profile-name')
                    reviewer_name = name_element.text.strip()
                except:
                    reviewer_name = "Anonyme"
                
                # Vérifier si cet avis a déjà été scrapé pour ce produit
                if reviewer_name in already_scraped_reviewers:
                    logger.info(f"Avis de '{reviewer_name}' déjà scrapé pour ce produit, ignoré")
                    continue
                
                # Initialiser un dictionnaire pour stocker les informations de l'avis
                review_data = {'asin': asin, 'reviewer': reviewer_name}
                
                # 2. Note (étoiles)
                try:
                    rating_element = review_element.find_element(By.CSS_SELECTOR, 'i[data-hook="review-star-rating"]')
                    rating_text = rating_element.get_attribute('textContent') or rating_element.text
                    rating_match = re.search(r'(\d+\.\d+|\d+)', rating_text)
                    review_data['rating'] = float(rating_match.group(1)) if rating_match else 0
                except:
                    try:
                        # Méthode alternative basée sur les classes
                        rating_element = review_element.find_element(By.CSS_SELECTOR, '[class*="a-star-"]')
                        star_class = rating_element.get_attribute('class')
                        star_class_match = re.search(r'a-star-(\d+)', star_class)
                        review_data['rating'] = float(star_class_match.group(1)) if star_class_match else 0
                    except:
                        review_data['rating'] = 0
                
                # 3. Titre de l'avis
                try:
                    title_element = review_element.find_element(By.CSS_SELECTOR, 'a[data-hook="review-title"]')
                    review_data['title'] = title_element.text.strip()
                except:
                    review_data['title'] = "Sans titre"
                
                # 4. Date et lieu de l'avis
                try:
                    date_element = review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="review-date"]')
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
                except:
                    review_data['location'] = "Unknown"
                    review_data['date'] = "Date inconnue"
                
                # 5. Achat vérifié
                try:
                    review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="avp-badge"]')
                    review_data['verified_purchase'] = True
                except:
                    review_data['verified_purchase'] = False
                
                # 6. Contenu de l'avis
                try:
                    review_body_element = review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="review-body"]')
                    review_data['comment'] = review_body_element.text.strip()
                except:
                    review_data['comment'] = "Aucun commentaire disponible"
                
                # 7. Nombre de personnes qui ont trouvé cet avis utile
                try:
                    helpful_element = review_element.find_element(By.CSS_SELECTOR, 'span[data-hook="helpful-vote-statement"]')
                    helpful_text = helpful_element.text.strip()
                    helpful_match = re.search(r'(\d+)', helpful_text)
                    review_data['helpful_count'] = int(helpful_match.group(1)) if helpful_match else 0
                except:
                    review_data['helpful_count'] = 0
                
                reviews.append(review_data)
                
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction d'un avis: {e}")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des avis: {e}")
    
    return reviews

def handle_captcha(driver):
    """Détecte et gère les CAPTCHA d'Amazon."""
    try:
        # Vérifier la présence d'un CAPTCHA
        if "captcha" in driver.current_url.lower() or driver.find_elements(By.ID, "captchacharacters"):
            logger.warning("CAPTCHA détecté! Le script ne peut pas continuer automatiquement.")
            
            # Attendre que l'utilisateur résolve le CAPTCHA manuellement
            input("Veuillez résoudre le CAPTCHA dans le navigateur puis appuyez sur Entrée pour continuer...")
            
            # Vérifier si le CAPTCHA a été résolu
            if "captcha" in driver.current_url.lower() or driver.find_elements(By.ID, "captchacharacters"):
                logger.error("Le CAPTCHA n'a pas été résolu. Abandon.")
                return False
            
            logger.info("CAPTCHA résolu, reprise du scraping.")
            return True
    except:
        pass
    
    return True  # Pas de CAPTCHA détecté

def save_reviews_to_csv(reviews, output_file):
    """Sauvegarde les avis dans un fichier CSV."""
    if not reviews:
        logger.info("Aucun nouvel avis à sauvegarder")
        return True
        
    try:
        file_exists = os.path.exists(output_file)
        
        # Créer le répertoire de sortie si nécessaire
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Ecrire en mode 'a' (append) si le fichier existe déjà, sinon en mode 'w'
        mode = 'a' if file_exists else 'w'
        with open(output_file, mode, newline='', encoding='utf-8') as f:
            # Définir les colonnes
            fieldnames = ['asin', 'reviewer', 'rating', 'title', 'date', 'location', 
                         'verified_purchase', 'comment', 'helpful_count']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Écrire l'en-tête uniquement si le fichier est nouveau
            if not file_exists:
                writer.writeheader()
            
            # Écrire les avis
            for review in reviews:
                writer.writerow({field: review.get(field, '') for field in fieldnames})
        
        logger.info(f"{len(reviews)} nouveaux avis sauvegardés dans {output_file}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des avis: {e}")
        return False

def scrape_reviews(url, max_reviews=50):
    """
    Scrape reviews for a single Amazon product.
    
    Args:
        url (str): The URL of the Amazon product page.
        max_reviews (int): Maximum number of reviews to scrape.
        
    Returns:
        list: A list of dictionaries containing review data.
    """
    try:
        # Extract ASIN from URL
        asin = extract_asin_from_url(url)
        if not asin:
            logger.error(f"Could not extract ASIN from URL: {url}")
            return []
            
        # Extract title from URL (basic version)
        title = url.split('/')[-1].replace('-', ' ').title()
        
        # Load already scraped reviews
        already_scraped = load_already_scraped_reviews()
        already_scraped_reviewers = already_scraped.get(asin, set())
        
        # Scrape reviews
        reviews = scrape_amazon_product_info(url, asin, title, already_scraped_reviewers)
        
        # Limit the number of reviews if needed
        if max_reviews and len(reviews) > max_reviews:
            reviews = reviews[:max_reviews]
            
        return reviews
        
    except Exception as e:
        logger.error(f"Error scraping reviews: {e}")
        return []

def main():
    """Fonction principale d'exécution."""
    # Créer le répertoire de données si nécessaire
    os.makedirs('data', exist_ok=True)
    
    # Charger les produits à scraper
    if not os.path.exists(PRODUCTS_CSV):
        logger.error(f"Le fichier {PRODUCTS_CSV} n'existe pas. Arrêt.")
        return
    
    # Charger la progression précédente
    progress = load_progress()
    last_index = progress.get("last_index", -1)
    
    # Charger les avis déjà scrapés
    already_scraped = load_already_scraped_reviews()
    
    # Lire le fichier CSV des produits
    try:
        products_df = pd.read_csv(PRODUCTS_CSV)
        logger.info(f"Chargé {len(products_df)} produits depuis {PRODUCTS_CSV}")
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier des produits: {e}")
        return
    
    # Parcourir chaque produit à partir du dernier index sauvegardé
    for i, row in products_df.iloc[last_index + 1:].iterrows():
        try:
            url = row['url']
            asin = row['asin']
            title = row['titre']
            
            # Vérifier si l'ASIN est valide
            if not asin or pd.isna(asin):
                asin = extract_asin_from_url(url)
                if not asin:
                    logger.warning(f"Impossible de trouver l'ASIN pour le produit à l'index {i}, URL: {url}")
                    continue
            
            # Récupérer les reviewers déjà scrapés pour ce produit
            already_scraped_reviewers = already_scraped.get(asin, set())
            
            # Si nous avons déjà scrapé ce produit et que l'utilisateur souhaite le sauter
            if asin in already_scraped and already_scraped_reviewers:
                logger.info(f"Produit {asin} déjà scrapé avec {len(already_scraped_reviewers)} avis. Vérification de nouveaux avis.")
            
            # Scraper les avis pour ce produit
            reviews = scrape_amazon_product_info(url, asin, title, already_scraped_reviewers)
            
            # Sauvegarder les nouveaux avis dans le CSV
            if reviews:
                save_reviews_to_csv(reviews, OUTPUT_CSV)
                
                # Mettre à jour les reviewers déjà scrapés
                if asin not in already_scraped:
                    already_scraped[asin] = set()
                for review in reviews:
                    already_scraped[asin].add(review['reviewer'])
            
            # Sauvegarder la progression
            save_progress(i)
            
            # Pause aléatoire entre les requêtes pour éviter la détection
            pause_time = random.uniform(5, 15)
            logger.info(f"Pause de {pause_time:.2f} secondes avant le prochain produit.")
            time.sleep(pause_time)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du produit à l'index {i}: {e}")
            # Sauvegarder la progression même en cas d'erreur
            save_progress(i)
    
    logger.info("Scraping terminé pour tous les produits!")

if __name__ == "__main__":
    main()