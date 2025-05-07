import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
import os
import pandas as pd

class AmazonProductScraper:
    def __init__(self, base_url="https://www.amazon.co.uk/s?i=computers&rh=n%3A429886031&s=popularity-rank&fs=true"):
        """
        Initialisation du scraper Amazon pour les listes de produits.

        Args:
            base_url (str): URL de base pour la recherche de produits.
        """
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.amazon.co.uk/'
        }
        self.products_file = 'amazon_products_all.csv'
        self.current_page = 0
        self.all_fields = []
        self.existing_asins = set()
        self.last_processed_page = 0

    def load_existing_products(self):
        """
        Charger les produits existants du fichier CSV pour éviter les doublons.
        Détermine également la dernière page traitée.
        """
        if os.path.exists(self.products_file) and os.path.getsize(self.products_file) > 0:
            try:
                df = pd.read_csv(self.products_file)
                if 'asin' in df.columns:
                    self.existing_asins = set(df['asin'].dropna())
                    print(f"{len(self.existing_asins)} ASINs existants chargés.")
                
                if 'page' in df.columns:
                    self.last_processed_page = max(df['page'].dropna().astype(int), default=0)
                    print(f"Dernière page traitée précédemment: {self.last_processed_page}")
                
                # Déterminer tous les champs possibles à partir du fichier existant
                self.all_fields = df.columns.tolist()
                print(f"Champs existants chargés: {self.all_fields}")
                
                return True
            except Exception as e:
                print(f"Erreur lors du chargement des produits existants: {e}")
                return False
        else:
            print("Aucun fichier existant trouvé, création d'un nouveau fichier.")
            return False

    def extract_product_info(self, product_element):
        """
        Extraire les informations d'un produit individuel.

        Args:
            product_element: Élément HTML du produit.

        Returns:
            dict: Informations du produit.
        """
        product_info = {}

        # Extraire le titre
        title_element = product_element.select_one('.a-size-base-plus.a-color-base.a-text-normal')
        if not title_element:
            title_element = product_element.select_one('.a-link-normal .a-text-normal')
        product_info['titre'] = title_element.text.strip() if title_element else "Titre non disponible"

        # Extraire l'URL du produit
        link_element = product_element.select_one('.a-link-normal')
        product_info['url'] = "https://www.amazon.co.uk" + link_element['href'] if link_element and 'href' in link_element.attrs else "URL non disponible"

        # Extraire le prix
        price_element = product_element.select_one('.a-price .a-offscreen')
        product_info['prix'] = price_element.text.strip() if price_element else "Prix non disponible"

        # Extraire la note
        rating_element = product_element.select_one('.a-icon-star-small')
        if rating_element:
            rating_text = rating_element.text.strip()
            product_info['note'] = rating_text
        else:
            product_info['note'] = "Note non disponible"

        # Extraire le nombre d'avis
        reviews_element = product_element.select_one('.a-size-small .a-link-normal')
        product_info['nombre_avis'] = reviews_element.text.strip() if reviews_element else "Nombre d'avis non disponible"

        # Extraire l'image
        img_element = product_element.select_one('img.s-image')
        product_info['image_url'] = img_element['src'] if img_element and 'src' in img_element.attrs else "Image non disponible"

        # ASIN (identifiant unique Amazon)
        asin = ""
        if 'data-asin' in product_element.attrs:
            asin = product_element['data-asin']
        else:
            # Essayer d'extraire l'ASIN de l'URL
            if product_info['url'] != "URL non disponible":
                asin_match = re.search(r'/dp/([A-Z0-9]{10})/', product_info['url'])
                if asin_match:
                    asin = asin_match.group(1)

        product_info['asin'] = asin if asin else "ASIN non disponible"

        # Ajouter le numéro de page comme information supplémentaire
        product_info['page'] = self.current_page

        return product_info

    def get_max_page_number(self, soup):
        """
        Extraire le numéro de la dernière page.

        Args:
            soup: Objet BeautifulSoup de la page.

        Returns:
            int: Numéro de la dernière page.
        """
        pagination_items = soup.select('.s-pagination-item')
        max_page = 1

        for item in pagination_items:
            if 'aria-disabled' in item.attrs and item.attrs['aria-disabled'] == 'true':
                try:
                    page_number = int(item.text.strip())
                    if page_number > max_page:
                        max_page = page_number
                except ValueError:
                    continue

        return max_page

    def scrape_page(self, url):
        """
        Scraper une page spécifique.

        Args:
            url (str): URL de la page à scraper.

        Returns:
            tuple: (objet BeautifulSoup, liste de produits)
        """
        try:
            # Faire la requête à la page
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Analyser le HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Trouver tous les produits de la page
            product_elements = soup.select('.s-result-item[data-component-type="s-search-result"]')

            print(f"Nombre de produits trouvés sur la page {self.current_page}: {len(product_elements)}")

            page_products = []
            skipped_count = 0

            for product in product_elements:
                product_info = self.extract_product_info(product)
                
                # Vérifier si le produit a un ASIN et s'il existe déjà
                if product_info['asin'] != "ASIN non disponible" and product_info['asin'] in self.existing_asins:
                    skipped_count += 1
                    continue
                
                if product_info['titre'] != "Titre non disponible":
                    page_products.append(product_info)
                    # Ajouter l'ASIN à la liste des existants pour éviter les doublons dans la même session
                    if product_info['asin'] != "ASIN non disponible":
                        self.existing_asins.add(product_info['asin'])

            print(f"Produits ignorés car déjà existants: {skipped_count}")
            return soup, page_products

        except Exception as e:
            print(f"Une erreur s'est produite lors du scraping de {url}: {e}")
            return None, []

    def initialize_csv_file(self, fieldnames, filename):
        """
        Initialiser un fichier CSV avec les en-têtes.

        Args:
            fieldnames (list): Liste des noms de colonnes.
            filename (str): Nom du fichier CSV.
        """
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    def append_to_csv(self, products, fieldnames, filename):
        """
        Ajouter des produits au fichier CSV existant.

        Args:
            products (list): Liste de dictionnaires contenant les produits.
            fieldnames (list): Liste des noms de colonnes.
            filename (str): Nom du fichier CSV.
        """
        # Si le fichier n'existe pas, l'initialiser
        if not os.path.exists(filename):
            self.initialize_csv_file(fieldnames, filename)
            
        with open(filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerows(products)

    def determine_all_fields(self, products):
        """
        Déterminer tous les champs possibles pour les en-têtes.

        Args:
            products (list): Liste de dictionnaires contenant les produits.

        Returns:
            list: Liste de tous les champs uniques.
        """
        all_keys = set(self.all_fields) if self.all_fields else set()
        for product in products:
            all_keys.update(product.keys())
        return list(all_keys)

    def scrape_all_pages(self, max_pages=None):
        """
        Scraper toutes les pages disponibles.

        Args:
            max_pages (int, optional): Nombre maximum de pages à scraper.

        Returns:
            bool: True si le scraping s'est terminé avec succès, False sinon.
        """
        # Charger les produits existants et la dernière page traitée
        file_exists = self.load_existing_products()
        
        # Déterminer la page de départ
        start_page = self.last_processed_page + 1 if self.last_processed_page > 0 else 1
        self.current_page = start_page
        
        print(f"Début du scraping à partir de la page {start_page}")

        # Si c'est la première page, déterminer le nombre total de pages
        if start_page == 1:
            # Commencer par la première page
            current_url = self.base_url
            soup, products = self.scrape_page(current_url)

            if not soup:
                print("Impossible d'accéder à la première page.")
                return False

            # Déterminer le nombre total de pages si non spécifié
            if not max_pages:
                max_pages = self.get_max_page_number(soup)

            # Déterminer tous les champs possibles
            self.all_fields = self.determine_all_fields(products)

            # Si nouveau fichier, initialiser le CSV avec les en-têtes
            if not file_exists:
                self.initialize_csv_file(self.all_fields, self.products_file)

            # Ajouter les produits de la première page
            if products:
                self.append_to_csv(products, self.all_fields, self.products_file)
                print(f"Page 1 traitée: {len(products)} produits ajoutés au fichier CSV")

            self.current_page += 1
        else:
            # Si on commence à une page ultérieure, vérifier max_pages
            if not max_pages:
                # Nécessite une requête à la première page pour obtenir le nombre total
                print("Vérification du nombre total de pages...")
                temp_soup, _ = self.scrape_page(self.base_url)
                if temp_soup:
                    max_pages = self.get_max_page_number(temp_soup)
                else:
                    print("Impossible de déterminer le nombre total de pages. Utilisation de la valeur par défaut: 20")
                    max_pages = 20

        print(f"Nombre total de pages à scraper: {max_pages}")
        print(f"Pages restantes à traiter: {max_pages - start_page + 1}")

        # Parcourir les pages suivantes
        success = True
        while self.current_page <= max_pages:
            # Construire l'URL de la page
            next_url = f"{self.base_url}&page={self.current_page}&qid=1745394762&ref=sr_pg_{self.current_page}"

            print(f"Scraping de la page {self.current_page}...")

            # Pause aléatoire pour éviter d'être détecté comme un robot
            time.sleep(random.uniform(2, 5))

            _, page_products = self.scrape_page(next_url)

            if page_products:
                # Mettre à jour les champs pour inclure de possibles nouveaux champs
                self.all_fields = self.determine_all_fields(page_products)
                
                # Ajouter les produits au fichier CSV
                self.append_to_csv(page_products, self.all_fields, self.products_file)
                print(f"Page {self.current_page} traitée: {len(page_products)} produits ajoutés au fichier CSV")
            else:
                print(f"Aucun produit trouvé sur la page {self.current_page} ou erreur lors du scraping")
                if self.current_page > start_page:  # Si au moins une page a été traitée avec succès
                    print("Continuation malgré l'erreur sur cette page...")
                else:
                    success = False
                    break

            self.current_page += 1

        return success

    def run_scraping(self, max_pages=None):
        """
        Exécuter le scraping des produits.

        Args:
            max_pages (int, optional): Nombre maximum de pages à scraper.

        Returns:
            bool: True si le processus s'est terminé avec succès, False sinon.
        """
        print(f"Début du scraping des produits Amazon UK vers le fichier {self.products_file}")

        # Récupérer les informations de base des produits
        success = self.scrape_all_pages(max_pages)

        if success:
            print(f"Scraping terminé avec succès! Tous les produits ont été sauvegardés dans {self.products_file}")
        else:
            print("Le scraping a échoué.")

        return success


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du scraper
    scraper = AmazonProductScraper()

    # Exécuter le scraping avec un maximum de 191 pages
    # Vous pouvez modifier le nombre de pages à scraper selon vos besoins
    scraper.run_scraping(max_pages=191)