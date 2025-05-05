import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

class AmazonDetailsScraper:
    def __init__(self, products_file='amazon_products_all.csv'):
        """
        Initialisation du scraper Amazon pour les détails techniques des produits.

        Args:
            products_file (str): Fichier CSV contenant les produits à analyser.
        """
        self.products_file = products_file
        self.details_file = 'product_information.csv'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.amazon.co.uk/'
        }

    def extract_technical_details(self, url, asin, titre):
        """
        Extraire les détails techniques d'un produit.

        Args:
            url (str): URL de la page du produit.
            asin (str): ASIN du produit.
            titre (str): Titre du produit.

        Returns:
            dict: Détails techniques du produit.
        """
        try:
            # Pause aléatoire pour éviter d'être bloqué
            time.sleep(random.uniform(2, 5))

            print(f"Extraction des détails pour: {titre} (ASIN: {asin})")

            # Faire la requête à la page du produit
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Analyser le HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Initialiser un dictionnaire pour stocker les détails techniques
            tech_details = {'asin': asin, 'titre': titre, 'url': url}

            # Trouver la table des spécifications techniques
            tech_table = soup.select_one('#productDetails_techSpec_section_1')

            if tech_table:
                # Extraire toutes les lignes de la table
                rows = tech_table.select('tr')

                for row in rows:
                    # Extraire l'en-tête et la valeur
                    header = row.select_one('th')
                    value = row.select_one('td')

                    if header and value:
                        # Nettoyer le texte
                        header_text = header.text.strip().replace('\n', ' ').replace('  ', ' ')
                        value_text = value.text.strip().replace('\n', ' ').replace('  ', ' ')

                        # Enlever les caractères de formatage ajoutés par Amazon
                        if value_text.startswith('‎'):
                            value_text = value_text[1:]

                        # Ajouter au dictionnaire
                        tech_details[header_text] = value_text
            else:
                print(f"Table des spécifications non trouvée pour ASIN: {asin}")

            return tech_details

        except Exception as e:
            print(f"Erreur lors de l'extraction des détails pour ASIN {asin}: {e}")
            return {'asin': asin, 'titre': titre, 'url': url, 'error': str(e)}

    def get_all_technical_details(self):
        """
        Extraire les détails techniques pour tous les produits du fichier CSV,
        en évitant ceux qui ont déjà été traités.

        Returns:
            bool: True si l'extraction s'est terminée avec succès, False sinon.
        """
        try:
            # Lire le fichier CSV contenant les URLs
            df = pd.read_csv(self.products_file)

            # Vérifier si le fichier de détails existe déjà
            already_processed_asins = set()
            if os.path.exists(self.details_file):
                try:
                    # Charger les données existantes
                    existing_details = pd.read_csv(self.details_file)
                    # Récupérer les ASINs déjà traités
                    if 'asin' in existing_details.columns:
                        already_processed_asins = set(existing_details['asin'].dropna().unique())
                        print(f"{len(already_processed_asins)} produits déjà traités trouvés dans le fichier existant.")
                    
                    # Charger toutes les données existantes pour les conserver
                    all_technical_details = existing_details.to_dict('records')
                except Exception as e:
                    print(f"Erreur lors de la lecture du fichier existant: {e}")
                    print("Création d'un nouveau fichier de détails.")
                    all_technical_details = []
            else:
                all_technical_details = []

            # Nombre total de produits à traiter
            total_products = len(df)
            print(f"Nombre total de produits dans le fichier source: {total_products}")
            
            # Filtrer les produits qui n'ont pas encore été traités
            to_process = df[~df['asin'].isin(already_processed_asins)]
            remaining_products = len(to_process)
            print(f"Nombre de produits restants à traiter: {remaining_products}")

            # Compter le nombre de produits traités dans cette session
            processed_this_session = 0

            # Pour chaque URL dans le fichier CSV qui n'a pas encore été traitée
            for index, row in to_process.iterrows():
                try:
                    asin = row['asin']
                    url = row['url']
                    titre = row['titre']

                    if asin == "ASIN non disponible" or url == "URL non disponible":
                        print(f"Données manquantes pour le produit à l'index {index}, on le saute")
                        continue
                        
                    # Vérifier encore une fois si l'ASIN est déjà traité (double vérification)
                    if asin in already_processed_asins:
                        print(f"ASIN {asin} déjà traité, on le saute")
                        continue

                    # Extraire les détails techniques
                    tech_details = self.extract_technical_details(url, asin, titre)

                    # Ajouter à la liste et marquer comme traité
                    if tech_details:
                        all_technical_details.append(tech_details)
                        already_processed_asins.add(asin)

                    # Mettre à jour le compteur
                    processed_this_session += 1

                    # Afficher la progression
                    if processed_this_session % 10 == 0 or processed_this_session == remaining_products:
                        print(f"Progression: {processed_this_session}/{remaining_products} produits traités dans cette session "
                              f"({(processed_this_session/remaining_products)*100:.2f}%)")

                        # Sauvegarder les données régulièrement
                        df_tech = pd.DataFrame(all_technical_details)
                        df_tech.to_csv(self.details_file, index=False, encoding='utf-8')
                        print(f"Sauvegarde effectuée dans {self.details_file}")

                except Exception as e:
                    print(f"Erreur lors du traitement de l'index {index}: {e}")
                    continue

            # Sauvegarder le fichier final
            df_tech = pd.DataFrame(all_technical_details)
            df_tech.to_csv(self.details_file, index=False, encoding='utf-8')

            total_processed = len(already_processed_asins)
            print(f"Extraction terminée! {processed_this_session} produits traités dans cette session.")
            print(f"Total de {total_processed}/{total_products} produits traités au total.")
            print(f"Les détails techniques ont été enregistrés dans {self.details_file}")
            
            return True

        except Exception as e:
            print(f"Erreur lors de l'extraction des détails techniques: {e}")
            return False

    def run_details_extraction(self):
        """
        Exécuter l'extraction des détails techniques.

        Returns:
            bool: True si le processus s'est terminé avec succès, False sinon.
        """
        print(f"Début de l'extraction des détails techniques vers le fichier {self.details_file}")
        
        # Extraire les détails techniques
        success = self.get_all_technical_details()

        if success:
            print("Extraction des détails techniques terminée avec succès!")
        else:
            print("L'extraction des détails techniques a échoué.")

        return success


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du scraper de détails
    details_scraper = AmazonDetailsScraper()

    # Exécuter l'extraction des détails techniques
    details_scraper.run_details_extraction()