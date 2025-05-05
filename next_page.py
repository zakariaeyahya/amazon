# scraper/amazon_next_page.py

import requests
from bs4 import BeautifulSoup

def scrape_next_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Affiche la pagination pour debug
            pagination = soup.select_one('ul.a-pagination')
            if not pagination:
                print("⚠️ Aucune pagination trouvée. Affichage du début du HTML pour debug:")
                print(response.text[:2000])  # début de la page pour vérif
                return "Pagination non trouvée dans la page."

            next_page_element = pagination.select_one('li.a-last a')

            if next_page_element and next_page_element.get('href'):
                next_page_href = next_page_element.get('href')
                full_url = "https://www.amazon.co.uk" + next_page_href
                return full_url
            else:
                return "Aucun lien 'Next page' trouvé."
        else:
            return f"Erreur HTTP: {response.status_code}"
    except Exception as e:
        return f"Erreur exception: {str(e)}"


# Exemple d'appel
if __name__ == "__main__":
    url = "https://www.amazon.co.uk/product-reviews/B0DNK1WFV6/ref=cm_cr_getr_d_paging_btm_next_2?ie=UTF8&reviewerType=all_reviews&pageNumber=2"
    next_page_link = scrape_next_page(url)
    print("Lien 'Next page':", next_page_link)
