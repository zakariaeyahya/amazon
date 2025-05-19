Pour ajouter du code HTML et CSS à votre fichier README sur GitHub, vous pouvez utiliser des balises HTML directement dans le fichier Markdown. Voici comment vous pouvez intégrer des styles CSS et du contenu HTML dans votre README :

```markdown
# Plateforme d'Extraction et d'Analyse de Produits Amazon

## Vision d'ensemble

Architecture distribuée d'extraction et d'analyse de données e-commerce optimisée pour Amazon, construite sur Python et Apache Airflow avec intégration Snowflake. Cette solution industrielle offre un pipeline complet de collecte, transformation et analyse de données produits à grande échelle.

## Capacités techniques

### Extraction de données
- **Collecte multi-catégories** avec traitement parallélisé
- **Extraction exhaustive**:
  - Métadonnées produits (identifiants, prix, spécifications)
  - Taxonomie des catégories et systèmes de filtrage
  - Données utilisateurs (avis, évaluations)
- **Mécanismes anti-blocage avancés**:
  - Gestion intelligente du throttling avec backoff exponentiel
  - Rotation d'agents utilisateurs et proxies
  - Modulation dynamique des taux de requêtes

### Traitement et pipeline
- **Orchestration via Apache Airflow** avec DAGs configurables
- **Parallélisation optimisée** via ThreadPoolExecutor
- **Exportation multi-formats** (CSV, JSON) avec validation structurelle
- **Observabilité intégrée** (métriques, logs structurés, rapports d'exécution)

### Analyse de données via Snowflake
- **Pipeline ETL** pour l'ingestion et la transformation des données
- **Modélisation analytique** avec tables normalisées et dénormalisées
- **Capacités analytiques avancées** incluant segmentation et analyse de sentiment

## Prérequis techniques

```html
<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px;">
    <p><strong>Python 3.8+</strong></p>
    <p><strong>Apache Airflow 2.5.0+</strong></p>
    <p><strong>PostgreSQL 13+</strong> (recommandé pour Airflow)</p>
    <p><strong>Snowflake</strong> (compte avec permissions adéquates)</p>
    <p><strong>AWS S3</strong> (stockage intermédiaire optionnel)</p>
</div>
```

## Dépendances

### Fondamentales
```html
<div style="background-color: #e8f4f8; padding: 10px; border-radius: 5px;">
    <p><strong>apache-airflow>=2.5.0</strong></p>
    <p><strong>requests>=2.28.0</strong></p>
    <p><strong>beautifulsoup4>=4.11.0</strong></p>
    <p><strong>pandas>=1.5.0</strong></p>
    <p><strong>selenium>=4.7.0</strong></p>
    <p><strong>webdriver-manager>=3.8.0</strong></p>
    <p><strong>python-dotenv>=0.21.0</strong></p>
    <p><strong>snowflake-connector-python>=2.7.0</strong></p>
</div>
```

## Déploiement

### Installation de l'environnement
```bash
# Clonage du référentiel
git clone <repository-url>
cd amazon-scraping

# Configuration de l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration d'Airflow
```bash
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

## Architecture de configuration

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

## Pipeline d'exécution

### Phase d'extraction
1. **Vérification préliminaire** - Validation de l'environnement et des dépendances
2. **Extraction des catégories** - Cartographie de la taxonomie produit
3. **Extraction des détails produits** - Collecte des métadonnées principales
4. **Extraction des avis** - Collecte des données utilisateurs
5. **Post-traitement** - Nettoyage et normalisation
6. **Génération de rapports** - Métriques d'exécution et validations

### Phase d'analyse Snowflake
1. **Chargement des données** - Ingestion dans les tables Snowflake
2. **Transformation** - Normalisation et enrichissement
3. **Modélisation** - Création des vues analytiques
4. **Segmentation** - Classification par prix et autres dimensions
5. **Analyse avancée** - Requêtes analytiques et rapports

## Architecture technique

```html
<div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px;">
    <pre>
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
    </pre>
</div>
```

## Modèle de données

### Tables principales
- `product_info1` - Données fondamentales produit
- `product_info2` - Spécifications techniques produit
- `review` - Avis et évaluations utilisateurs
- `full_product_info` - Vue dénormalisée intégrée
- `classe_prix` - Segmentation par gamme de prix

## Exemples d'analyses

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

## Résolution des problèmes courants

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

## Sécurité et conformité

Ce projet est conçu pour un usage professionnel et éducatif. L'utilisation doit être conforme aux:
- Conditions d'utilisation d'Amazon
- Directives du fichier robots.txt
- Réglementations en vigueur sur la protection des données

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier LICENSE pour plus de détails.

