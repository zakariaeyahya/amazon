import requests
from bs4 import BeautifulSoup
import json
import time
import re

def scrape_amazon_filters(category=None, max_pages=5, max_products=100, output_file='amazon_filters.json'):
    # URL de la page Amazon à scraper
    base_url = "https://www.amazon.co.uk/s"
    params = {
        'i': category if category else 'computers',
        'rh': 'n%3A429886031',
        's': 'popularity-rank',
        'fs': 'true'
    }
    url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    # En-têtes pour imiter un navigateur (nécessaire pour éviter les blocages)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    try:
        # Faire la requête HTTP
        print(f"Envoi de la requête à Amazon UK pour la catégorie {category}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("Requête réussie, analyse du HTML...")
        
        # Parser le HTML avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Dictionnaire pour stocker toutes les catégories et leurs valeurs
        filtered_data = {
            'category': category,
            'product_urls': [],
            'filters': {}
        }
        
        # Trouver tous les titres de catégories avec la classe spécifique
        category_titles = soup.find_all('span', class_='a-size-base a-color-base puis-bold-weight-text')
        
        # Initialiser la liste pour stocker les sections de filtres
        filter_sections = []
        
        # Pour chaque titre de catégorie, trouver la section associée
        for title_span in category_titles:
            category_name = title_span.text.strip()
            
            # Trouver le parent contenant le titre et les valeurs
            parent_section = title_span
            # Remonter jusqu'à trouver le div de la section complète
            while parent_section and not (parent_section.name == 'div' and 'a-section' in parent_section.get('class', [])):
                parent_section = parent_section.parent
            
            if parent_section:
                filter_sections.append({
                    'name': category_name,
                    'section': parent_section
                })
        
        # Traiter chaque section pour en extraire les valeurs
        for i, section_data in enumerate(filter_sections):
            category_name = section_data['name']
            section = section_data['section']
            
            print(f"\nCatégorie trouvée: {category_name}")
            
            # Initialiser une liste pour stocker les valeurs de cette catégorie
            category_values = []
            
            # Déterminer jusqu'où chercher (jusqu'à la prochaine section ou la fin du document)
            next_section = None
            if i < len(filter_sections) - 1:
                next_section = filter_sections[i + 1]['section']
            
            # Chercher d'abord la liste ul qui contient les valeurs
            ul_element = None
            # Parcourir les éléments suivants de la section actuelle
            for sibling in section.find_all_next():
                # Si on atteint la section suivante, on s'arrête
                if next_section and sibling == next_section:
                    break
                # Si on trouve une liste ul, c'est probablement celle qui contient nos valeurs
                if sibling.name == 'ul' and 'a-unordered-list' in sibling.get('class', []):
                    ul_element = sibling
                    break
            
            # Si on a trouvé une liste, extraire les valeurs
            if ul_element:
                list_items = ul_element.find_all('span', class_='a-list-item')
                
                # Parcourir chaque élément de liste
                for item in list_items:
                    # Chercher le lien dans l'élément
                    link = item.find('a', class_='a-link-normal s-navigation-item')
                    
                    if link:
                        # Chercher le nom de la valeur dans le lien
                        value_span = link.find('span', class_='a-size-base a-color-base')
                        
                        if value_span:
                            value_name = value_span.text.strip()
                            value_url = "https://www.amazon.co.uk" + link.get('href')
                            
                            # Extraire l'ID du filtre depuis l'URL
                            filter_key = None
                            filter_value = None
                            
                            try:
                                # Utiliser regex pour extraire les paramètres
                                if 'rh=' in value_url:
                                    rh_part = value_url.split('rh=')[1].split('&')[0]
                                    # Convertir les caractères encodés
                                    rh_part = rh_part.replace('%3A', ':').replace('%2C', ',')
                                    # Chercher les parties p_XXX:YYYY
                                    filter_parts = re.findall(r'([p|n]_[^:,]+):([^,]+)', rh_part)
                                    
                                    # Trouver la partie qui diffère de l'URL de base
                                    base_filters = set(re.findall(r'([p|n]_[^:,]+):([^,]+)', url.split('rh=')[1].split('&')[0].replace('%3A', ':').replace('%2C', ',')))
                                    
                                    for key, val in filter_parts:
                                        if (key, val) not in base_filters:
                                            filter_key = key
                                            filter_value = val
                                            break
                            except Exception as e:
                                print(f"  Erreur lors de l'extraction des filtres: {e}")
                            
                            filter_data = {
                                "name": value_name,
                                "url": value_url
                            }
                            
                            if filter_key and filter_value:
                                filter_data["filter_key"] = filter_key
                                filter_data["filter_value"] = filter_value
                            
                            category_values.append(filter_data)
                            print(f"  Valeur trouvée: {value_name}")
                            if filter_key and filter_value:
                                print(f"    Clé: {filter_key}, Valeur: {filter_value}")
            
            # Ajouter les valeurs à la catégorie
            if category_values:
                filtered_data['filters'][category_name] = category_values
        
        # Enregistrer les résultats dans un fichier JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nLes données ont été enregistrées dans '{output_file}'")
        
        # Afficher le JSON dans la console pour vérification
        print("\nPrévisualisation du JSON:")
        print(json.dumps(filtered_data, indent=2, ensure_ascii=False))
        
        return filtered_data
    
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête HTTP: {e}")
        return None
    except Exception as e:
        print(f"Une erreur s'est produite: {e}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print("Démarrage du scraping des filtres d'ordinateurs sur Amazon UK...")
    scrape_amazon_filters()