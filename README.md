# 🚀 Plateforme d'Extraction et d'Analyse de Produits Amazon

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Airflow](https://img.shields.io/badge/Airflow-2.5.0%2B-red)
![Snowflake](https://img.shields.io/badge/Snowflake-Ready-9cf)
![License](https://img.shields.io/badge/License-MIT-green)

> Architecture distribuée d'extraction et d'analyse de données e-commerce optimisée pour Amazon, construite sur Python et Apache Airflow avec intégration Snowflake.

## 🔍 Présentation

Cette plateforme permet l'extraction et l'analyse de données produits depuis Amazon, en offrant une solution complète et performante grâce à une architecture distribuée et scalable.

**Capacités principales:**
- Collecte multi-catégories avec traitement parallélisé
- Extraction exhaustive des métadonnées produits, taxonomie et avis utilisateurs
- Systèmes anti-blocage avancés
- Pipeline d'analyse complet via Snowflake

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Pipeline d'exécution](#-pipeline-dexécution)
- [Modèle de données](#-modèle-de-données)
- [Exemples d'utilisation](#-exemples-dutilisation)
- [Résolution des problèmes](#-résolution-des-problèmes)
- [Sécurité et conformité](#-sécurité-et-conformité)
- [Performance](#-performance-et-optimisation)
- [Développements futurs](#-développements-futurs)
- [Licence](#-licence)

## ✨ Fonctionnalités

### 🔍 Extraction de données
- **Collecte multi-catégories**: Système optimisé pour extraire des données de plusieurs catégories Amazon simultanément
- **Extraction exhaustive**:
  - Métadonnées produits (identifiants, prix, spécifications)
  - Taxonomie des catégories et systèmes de filtrage
  - Données utilisateurs (avis, évaluations)
- **Anti-blocage avancé**:
  - Gestion intelligente du throttling avec backoff exponentiel
  - Rotation d'agents utilisateurs et proxies
  - Modulation dynamique des taux de requêtes

### ⚙️ Traitement et pipeline
- **Orchestration via Apache Airflow**: Gestion complète du workflow avec DAGs configurables
- **Parallélisation optimisée**: Utilisation de ThreadPoolExecutor pour maximiser l'efficacité
- **Exportation multi-formats**: Support des formats CSV et JSON avec validation structurelle
- **Observabilité intégrée**: Système complet de métriques, logs structurés et rapports d'exécution

### 📊 Analyse de données via Snowflake
- **Pipeline ETL**: Système d'ingestion et transformation automatisé
- **Modélisation analytique**: Tables normalisées et dénormalisées pour différents cas d'usage
- **Capacités analytiques**: Segmentation produit, analyse de sentiment et autres fonctionnalités

## 📋 Prérequis

- Python 3.8+
- Apache Airflow 2.5.0+
- PostgreSQL 13+ (recommandé pour Airflow)
- Compte Snowflake avec permissions adéquates
- *(Optionnel)* AWS S3 pour le stockage intermédiaire des données extraites

### Dépendances Python

```
apache-airflow>=2.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
selenium>=4.7.0
webdriver-manager>=3.8.0
python-dotenv>=0.21.0
snowflake-connector-python>=2.7.0
```

## 🔧 Installation

```bash
# Clonage du référentiel
git clone https://github.com/zakariaeyahya/amazon.git
cd amazon-scraping

# Configuration de l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Définition du répertoire home d'Airflow
export AIRFLOW_HOME=/path/to/airflow

# Initialisation de la base de données
airflow db init

# Création de l'utilisateur administrateur
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password your_password

# Configuration des répertoires nécessaires
mkdir -p $AIRFLOW_HOME/{dags,logs,plugins}
```

## 🏗️ Architecture

```
amazon-analytics/
├── airflow_dags/
│   └── amazon_scraping_dag.py
├── scrapers/
│   ├── categories.py
│   ├── amazon_details_scraper.py
│   ├── commentaire.py
│   └── scraping.py
├── utils/
│   ├── file_utils.py
│   ├── scraping_logger.py
│   └── scraping_metrics.py
├── snowflake/
│   ├── SQLrequet.sql
│   └── snowflakeconnection.py
├── data/
├── logs/
├── config/
├── tests/
└── requirements.txt
```

## ⚙️ Configuration

### Configuration de l'extracteur

```json
{
  "extraction": {
    "categories": ["electronics", "computers", "smart-home"],
    "limites": {
      "produits_par_categorie": 100,
      "pages_par_categorie": 5
    },
    "controle_debit": {
      "requetes_par_seconde": 2,
      "taille_burst": 5,
      "delai_apres_echec": 300
    },
    "proxies": {
      "actifs": true,
      "liste": [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080"
      ],
      "intervalle_rotation": 100
    },
    "agents_utilisateurs": {
      "actifs": true,
      "intervalle_rotation": 50
    }
  },
  "traitement": {
    "taille_lot": 5,
    "travailleurs_max": 2
  }
}
```

### Configuration Snowflake

```python
# snowflakeconnection.py
conn_config = {
    'user': 'SNOWFLAKE_USER',
    'password': 'SNOWFLAKE_PASSWORD',
    'account': 'SNOWFLAKE_ACCOUNT',
    'warehouse': 'COMPUTE_WH',
    'database': 'AMAZON_ANALYTICS',
    'schema': 'PUBLIC'
}
```

## 🔄 Pipeline d'exécution

### Phase d'extraction
1. Vérification préliminaire - Validation de l'environnement et des dépendances
2. Extraction des catégories - Cartographie de la taxonomie produit
3. Extraction des détails produits - Collecte des métadonnées principales
4. Extraction des avis - Collecte des données utilisateurs
5. Post-traitement - Nettoyage et normalisation
6. Génération de rapports - Métriques d'exécution et validations

### Phase d'analyse Snowflake
1. Chargement des données - Ingestion dans les tables Snowflake
2. Transformation - Normalisation et enrichissement
3. Modélisation - Création des vues analytiques
4. Segmentation - Classification par prix et autres dimensions
5. Analyse avancée - Requêtes analytiques et rapports

## 💾 Modèle de données

### Tables principales

| Table | Description |
|-------|-------------|
| `product_info1` | Données fondamentales produit |
| `product_info2` | Spécifications techniques produit |
| `review` | Avis et évaluations utilisateurs |
| `full_product_info` | Vue dénormalisée intégrée |
| `classe_prix` | Segmentation par gamme de prix |

> **Note:** Le schéma est conçu pour optimiser à la fois les requêtes analytiques et les opérations OLTP.

## 💡 Exemples d'utilisation

### Classification de produits et analyse de sentiment

```sql
SELECT
    p.asin,
    p.titre,
    p.prix,
    c.classe AS gamme_prix,
    r.sentiment,
    COUNT(r.review_id) AS nombre_avis
FROM
    full_product_info p
JOIN
    classe_prix c ON p.asin = c.asin
LEFT JOIN
    review r ON p.asin = r.asin
GROUP BY
    1, 2, 3, 4, 5
ORDER BY
    nombre_avis DESC;
```

### Transformation des spécifications techniques

```sql
-- Normalisation des tailles de disque dur en GB
UPDATE product_info2
SET disque_dur =
    CASE
        WHEN disque_dur LIKE '%TB%' THEN TO_NUMBER(REGEXP_SUBSTR(disque_dur, '[0-9]+')) * 1024
        WHEN disque_dur LIKE '%GB%' THEN TO_NUMBER(REGEXP_SUBSTR(disque_dur, '[0-9]+'))
        ELSE NULL
    END;
```

## 🔧 Résolution des problèmes

### DAGs Airflow
- Vérifier les permissions des fichiers DAG
- Valider la syntaxe Python avec `airflow dags list` et `airflow dags show`
- Consulter les logs pour erreurs de syntaxe ou d'importation

### Limitations de taux
- Implémenter une stratégie de backoff progressif
- Augmenter l'intervalle entre requêtes
- Diversifier les proxies et agents utilisateurs

### Connexion Snowflake
- Vérifier les identifiants et permissions
- S'assurer que l'adresse IP est autorisée
- Tester la connexion avec une requête simple

## 🔒 Sécurité et conformité

⚠️ **Important:** Ce projet est conçu pour un usage professionnel et éducatif. L'utilisation doit être conforme aux:
- Conditions d'utilisation d'Amazon
- Directives du fichier robots.txt
- Réglementations en vigueur sur la protection des données

### Bonnes pratiques de sécurité
- Ne jamais stocker les identifiants en clair dans le code
- Utiliser des variables d'environnement ou un gestionnaire de secrets
- Implémenter une politique de limitation de requêtes raisonnable
- Auditer régulièrement les logs d'accès
- Chiffrer les données sensibles lors du stockage et du transit


## 📜 Licence

Ce projet est distribué sous [licence MIT](LICENSE).

---

© 2025 - Plateforme d'Extraction et d'Analyse de Produits Amazon - Tous droits réservés
