<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Analytics - Documentation</title>
    <style>
        :root {
            --primary: #232f3e;
            --secondary: #ff9900;
            --success: #37bd6c;
            --info: #36c2f8;
            --warning: #ffcc00;
            --danger: #e94a35;
            --light: #f8f9fa;
            --dark: #2a3039;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, #131921 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 40px;
            box-shadow: 0 10px 20px rgba(35, 47, 62, 0.15);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: "";
            position: absolute;
            top: -20px;
            right: -20px;
            width: 180px;
            height: 180px;
            background: var(--secondary);
            border-radius: 50%;
            opacity: 0.3;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            position: relative;
            z-index: 1;
        }
        
        .header p {
            margin: 10px 0 0;
            font-size: 1.2rem;
            font-weight: 300;
            max-width: 80%;
            position: relative;
            z-index: 1;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 10px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
            border-radius: 20px;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .badge-primary {
            background-color: var(--primary);
            color: white;
        }
        
        .badge-secondary {
            background-color: var(--secondary);
            color: white;
        }
        
        .badge-info {
            background-color: var(--info);
            color: white;
        }
        
        section {
            background-color: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease;
        }
        
        section:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        h2 {
            color: var(--primary);
            border-bottom: 2px solid var(--secondary);
            padding-bottom: 10px;
            margin-top: 0;
            display: flex;
            align-items: center;
        }
        
        h2::before {
            content: "⚙️";
            margin-right: 10px;
            font-size: 1.5rem;
        }
        
        .extraction h2::before { content: "🔍"; }
        .traitement h2::before { content: "⚙️"; }
        .analyse h2::before { content: "📊"; }
        .prerequis h2::before { content: "📋"; }
        .dependances h2::before { content: "🧩"; }
        .deploiement h2::before { content: "🚀"; }
        .architecture h2::before { content: "🏗️"; }
        .config h2::before { content: "⚙️"; }
        .pipeline h2::before { content: "🔄"; }
        .modele h2::before { content: "💾"; }
        .exemples h2::before { content: "💡"; }
        .problemes h2::before { content: "🔧"; }
        .securite h2::before { content: "🔒"; }
        .licence h2::before { content: "📜"; }
        
        h3 {
            color: var(--dark);
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        li {
            padding: 5px 0;
            position: relative;
            padding-left: 30px;
        }
        
        li::before {
            content: "▶";
            color: var(--secondary);
            position: absolute;
            left: 0;
            font-size: 0.8rem;
        }
        
        li ul {
            padding-left: 20px;
        }
        
        .feature-box {
            background-color: #f7f7f7;
            border-left: 5px solid var(--secondary);
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        
        .code-block {
            background-color: var(--dark);
            color: #ffffff;
            padding: 15px;
            margin: 15px 0;
            border-radius: 6px;
            overflow-x: auto;
            position: relative;
        }
        
        .code-block::before {
            content: attr(data-language);
            position: absolute;
            top: 0;
            right: 10px;
            background-color: var(--secondary);
            color: white;
            padding: 2px 8px;
            font-size: 0.7rem;
            border-radius: 0 0 4px 4px;
            text-transform: uppercase;
        }
        
        .code-block pre {
            margin: 0;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
        }
        
        .row {
            display: flex;
            flex-wrap: wrap;
            margin: -10px;
        }
        
        .col {
            flex: 1;
            padding: 10px;
            min-width: 250px;
        }
        
        .card {
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            border-top: 5px solid var(--primary);
        }
        
        .card-header {
            background-color: #f7f7f7;
            padding: 15px;
            font-weight: bold;
        }
        
        .card-body {
            padding: 15px;
        }
        
        .alert {
            padding: 15px;
            margin: 15px 0;
            border-radius: 6px;
            position: relative;
            border-left: 5px solid;
        }
        
        .alert-warning {
            background-color: rgba(255, 204, 0, 0.1);
            border-color: var(--warning);
        }
        
        .alert-info {
            background-color: rgba(54, 194, 248, 0.1);
            border-color: var(--info);
        }
        
        .alert-danger {
            background-color: rgba(233, 74, 53, 0.1);
            border-color: var(--danger);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        table th {
            background-color: var(--primary);
            color: white;
            padding: 10px;
            text-align: left;
        }
        
        table td {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .progress-container {
            width: 100%;
            background-color: #e9ecef;
            border-radius: 10px;
            margin: 15px 0;
            overflow: hidden;
        }
        
        .progress-bar {
            width: 75%;
            height: 10px;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            border-radius: 10px;
        }
        
        .timeline {
            position: relative;
            padding-left: 30px;
            margin-bottom: 20px;
        }
        
        .timeline::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            width: 2px;
            background-color: var(--secondary);
        }
        
        .timeline-item {
            position: relative;
            padding: 0 0 20px 20px;
        }
        
        .timeline-item::before {
            content: "";
            position: absolute;
            left: -9px;
            top: 0;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: var(--secondary);
        }
        
        .timeline-item:last-child {
            padding-bottom: 0;
        }
        
        .timeline-item h4 {
            margin: 0 0 5px 0;
        }
        
        .timeline-item p {
            margin: 0;
        }
        
        .tech-icon {
            background-color: #f7f7f7;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px auto;
            font-size: 1.8rem;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background-color: var(--primary);
            color: white;
            border-radius: 8px;
        }

        /* Animations */
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .animated-pulse {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>

<div class="header">
    <h1>Plateforme d'Extraction et d'Analyse de Produits Amazon</h1>
    <p>Architecture distribuée d'extraction et d'analyse de données e-commerce optimisée pour Amazon, construite sur Python et Apache Airflow avec intégration Snowflake.</p>
    <div style="margin-top: 20px;">
        <span class="badge badge-primary">Python</span>
        <span class="badge badge-secondary">Airflow</span>
        <span class="badge badge-info">Snowflake</span>
        <span class="badge badge-primary">Data Engineering</span>
        <span class="badge badge-secondary">Web Scraping</span>
    </div>
</div>

<section class="extraction">
    <h2>Capacités d'extraction de données</h2>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">Collecte multi-catégories</div>
                <div class="card-body">
                    <p>Système de traitement parallélisé optimisé pour extraire des données de plusieurs catégories Amazon simultanément.</p>
                    <div class="progress-container">
                        <div class="progress-bar"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Extraction exhaustive</div>
                <div class="card-body">
                    <ul>
                        <li>Métadonnées produits (identifiants, prix, spécifications)</li>
                        <li>Taxonomie des catégories et systèmes de filtrage</li>
                        <li>Données utilisateurs (avis, évaluations)</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Anti-blocage avancé</div>
                <div class="card-body">
                    <ul>
                        <li>Gestion intelligente du throttling avec backoff exponentiel</li>
                        <li>Rotation d'agents utilisateurs et proxies</li>
                        <li>Modulation dynamique des taux de requêtes</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="traitement">
    <h2>Traitement et pipeline</h2>
    
    <div class="feature-box">
        <h3>Orchestration via Apache Airflow</h3>
        <p>Gestion complète du workflow avec DAGs configurables pour chaque étape du processus d'extraction et d'analyse.</p>
    </div>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">Parallélisation optimisée</div>
                <div class="card-body">
                    <p>Utilisation de ThreadPoolExecutor pour maximiser l'efficacité des opérations d'extraction tout en minimisant l'impact sur les serveurs cibles.</p>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Exportation multi-formats</div>
                <div class="card-body">
                    <p>Support des formats CSV et JSON avec validation structurelle automatique pour garantir l'intégrité des données.</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="feature-box">
        <h3>Observabilité intégrée</h3>
        <p>Système complet de métriques, logs structurés et rapports d'exécution pour un suivi en temps réel des opérations.</p>
    </div>
</section>

<section class="analyse">
    <h2>Analyse de données via Snowflake</h2>
    
    <div class="row">
        <div class="col">
            <div class="timeline">
                <div class="timeline-item">
                    <h4>Pipeline ETL</h4>
                    <p>Système d'ingestion et transformation automatisé des données extraites.</p>
                </div>
                
                <div class="timeline-item">
                    <h4>Modélisation analytique</h4>
                    <p>Conception de tables normalisées et dénormalisées pour différents cas d'usage.</p>
                </div>
                
                <div class="timeline-item">
                    <h4>Capacités analytiques</h4>
                    <p>Segmentation produit, analyse de sentiment et autres fonctionnalités avancées.</p>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Avantages Snowflake</div>
                <div class="card-body">
                    <ul>
                        <li>Performance de requête optimisée</li>
                        <li>Séparation stockage/calcul</li>
                        <li>Scaling automatique selon la charge</li>
                        <li>Partage de données sécurisé</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="prerequis">
    <h2>Prérequis techniques</h2>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-body" style="text-align: center;">
                    <div class="tech-icon">🐍</div>
                    <h3>Python 3.8+</h3>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-body" style="text-align: center;">
                    <div class="tech-icon">🌪️</div>
                    <h3>Apache Airflow 2.5.0+</h3>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-body" style="text-align: center;">
                    <div class="tech-icon">🐘</div>
                    <h3>PostgreSQL 13+</h3>
                    <p>Recommandé pour Airflow</p>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-body" style="text-align: center;">
                    <div class="tech-icon">❄️</div>
                    <h3>Snowflake</h3>
                    <p>Compte avec permissions adéquates</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="alert alert-info">
        <strong>Optionnel:</strong> AWS S3 pour le stockage intermédiaire des données extraites.
    </div>
</section>

<section class="dependances">
    <h2>Dépendances</h2>
    
    <div class="code-block" data-language="txt">
<pre>
apache-airflow>=2.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
selenium>=4.7.0
webdriver-manager>=3.8.0
python-dotenv>=0.21.0
snowflake-connector-python>=2.7.0
</pre>
    </div>
</section>

<section class="deploiement">
    <h2>Déploiement</h2>
    
    <div class="card">
        <div class="card-header">Installation de l'environnement</div>
        <div class="card-body">
            <div class="code-block" data-language="bash">
<pre>
# Clonage du référentiel
git clone <repository-url>
cd amazon-scraping

# Configuration de l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
</pre>
            </div>
        </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
        <div class="card-header">Configuration d'Airflow</div>
        <div class="card-body">
            <div class="code-block" data-language="bash">
<pre>
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
</pre>
            </div>
        </div>
    </div>
</section>

<section class="config">
    <h2>Architecture de configuration</h2>
    
    <div class="row">
        <div class="col">
            <h3>Configuration de l'extracteur</h3>
            <div class="code-block" data-language="json">
<pre>
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
</pre>
            </div>
        </div>
        
        <div class="col">
            <h3>Configuration Snowflake</h3>
            <div class="code-block" data-language="python">
<pre>
# snowflakeconnection.py
conn_config = {
    'user': 'SNOWFLAKE_USER',
    'password': 'SNOWFLAKE_PASSWORD',
    'account': 'SNOWFLAKE_ACCOUNT',
    'warehouse': 'COMPUTE_WH',
    'database': 'AMAZON_ANALYTICS',
    'schema': 'PUBLIC'
}
</pre>
            </div>
        </div>
    </div>
</section>

<section class="pipeline">
    <h2>Pipeline d'exécution</h2>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">Phase d'extraction</div>
                <div class="card-body">
                    <ol>
                        <li>Vérification préliminaire - Validation de l'environnement et des dépendances</li>
                        <li>Extraction des catégories - Cartographie de la taxonomie produit</li>
                        <li>Extraction des détails produits - Collecte des métadonnées principales</li>
                        <li>Extraction des avis - Collecte des données utilisateurs</li>
                        <li>Post-traitement - Nettoyage et normalisation</li>
                        <li>Génération de rapports - Métriques d'exécution et validations</li>
                    </ol>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Phase d'analyse Snowflake</div>
                <div class="card-body">
                    <ol>
                        <li>Chargement des données - Ingestion dans les tables Snowflake</li>
                        <li>Transformation - Normalisation et enrichissement</li>
                        <li>Modélisation - Création des vues analytiques</li>
                        <li>Segmentation - Classification par prix et autres dimensions</li>
                        <li>Analyse avancée - Requêtes analytiques et rapports</li>
                    </ol>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="architecture">
    <h2>Architecture technique</h2>
    
    <div class="code-block" data-language="structure">
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
</section>

<section class="modele">
    <h2>Modèle de données</h2>
    
    <h3>Tables principales</h3>
    <table>
        <thead>
            <tr>
                <th>Table</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><code>product_info1</code></td>
                <td>Données fondamentales produit</td>
            </tr>
            <tr>
                <td><code>product_info2</code></td>
                <td>Spécifications techniques produit</td>
            </tr>
            <tr>
                <td><code>review</code></td>
                <td>Avis et évaluations utilisateurs</td>
            </tr>
            <tr>
                <td><code>full_product_info</code></td>
                <td>Vue dénormalisée intégrée</td>
            </tr>
            <tr>
                <td><code>classe_prix</code></td>
                <td>Segmentation par gamme de prix</td>
            </tr>
        </tbody>
    </table>
    
    <div class="alert alert-info">
        <strong>Note:</strong> Le schéma est conçu pour optimiser à la fois les requêtes analytiques et les opérations OLTP.
    </div>
</section>

<section class="exemples">
    <h2>Exemples d'analyses</h2>
    
    <div class="card">
        <div class="card-header">Classification de produits et analyse de sentiment</div>
        <div class="card-body">
            <div class="code-block" data-language="sql">
<pre>
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
</pre>
            </div>
        </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
        <div class="card-header">Transformation des spécifications techniques</div>
        <div class="card-body">
            <div class="code-block" data-language="sql">
<pre>
-- Normalisation des tailles de disque dur en GB
UPDATE product_info2
SET disque_dur =
    CASE
        WHEN disque_dur LIKE '%TB%' THEN TO_NUMBER(REGEXP_SUBSTR(disque_dur, '[0-9]+')) * 1024
        WHEN disque_dur LIKE '%GB%' THEN TO_NUMBER(REGEXP_SUBSTR(disque_dur, '[0-9]+'))
        ELSE NULL
    END;
</pre>
            </div>
        </div>
    </div>
</section>

<section class="problemes">
    <h2>Résolution des problèmes courants</h2>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">DAGs Airflow</div>
                <div class="card-body">
                    <ul>
                        <li>Vérifier les permissions des fichiers DAG</li>
                        <li>Valider la syntaxe Python avec <code>airflow dags list</code> et <code>airflow dags show</code></li>
                        <li>Consulter les logs pour erreurs de syntaxe ou d'importation</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Limitations de taux</div>
                <div class="card-body">
                    <ul>
                        <li>Implémenter une stratégie de backoff progressif</li>
                        <li>Augmenter l'intervalle entre requêtes</li>
                        <li>Diversifier les proxies et agents utilisateurs</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Connexion Snowflake</div>
                <div class="card-body">
                    <ul>
                        <li>Vérifier les identifiants et permissions</li>
                        <li>S'assurer que l'adresse IP est autorisée</li>
                        <li>Tester la connexion avec une requête simple</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="securite">
    <h2>Sécurité et conformité</h2>
    
    <div class="alert alert-warning">
        <p>Ce projet est conçu pour un usage professionnel et éducatif. L'utilisation doit être conforme aux:</p>
        <ul>
            <li>Conditions d'utilisation d'Amazon</li>
            <li>Directives du fichier robots.txt</li>
            <li>Réglementations en vigueur sur la protection des données</li>
        </ul>
    </div>
    
    <div class="feature-box">
        <h3>Bonnes pratiques de sécurité</h3>
        <ul>
            <li>Ne jamais stocker les identifiants en clair dans le code</li>
            <li>Utiliser des variables d'environnement ou un gestionnaire de secrets</li>
            <li>Implémenter une politique de limitation de requêtes raisonnable</li>
            <li>Auditer régulièrement les logs d'accès</li>
            <li>Chiffrer les données sensibles lors du stockage et du transit</li>
        </ul>
    </div>
</section>

<section class="licence">
    <h2>Licence</h2>
    
    <div class="card animated-pulse">
        <div class="card-body" style="text-align: center;">
            <h3>MIT License</h3>
            <p>Ce projet est distribué sous licence MIT.</p>
            <p>Voir le fichier LICENSE pour plus de détails.</p>
        </div>
    </div>
</section>

<section>
    <h2>Démarrage rapide</h2>
    
    <div class="timeline">
        <div class="timeline-item">
            <h4>1. Installation</h4>
            <p>Suivez les instructions de la section Déploiement pour configurer l'environnement</p>
        </div>
        
        <div class="timeline-item">
            <h4>2. Configuration</h4>
            <p>Adaptez les fichiers de configuration à vos besoins spécifiques</p>
        </div>
        
        <div class="timeline-item">
            <h4>3. Lancement d'Airflow</h4>
            <p>Exécutez <code>airflow webserver</code> et <code>airflow scheduler</code> dans des terminaux séparés</p>
        </div>
        
        <div class="timeline-item">
            <h4>4. Activation des DAGs</h4>
            <p>Activez les DAGs requis via l'interface web d'Airflow</p>
        </div>
        
        <div class="timeline-item">
            <h4>5. Analyse des résultats</h4>
            <p>Explorez les données extraites via Snowflake ou les fichiers CSV/JSON générés</p>
        </div>
    </div>
</section>

<section>
    <h2>Visualisation des données</h2>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">Tableau de bord intégré</div>
                <div class="card-body">
                    <p>Un tableau de bord basé sur Streamlit est inclus pour visualiser rapidement les données extraites:</p>
                    <div class="code-block" data-language="bash">
<pre>
# Installation de Streamlit
pip install streamlit

# Lancement du tableau de bord
cd amazon-analytics
streamlit run dashboard/main.py
</pre>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Intégration BI externe</div>
                <div class="card-body">
                    <p>Les données peuvent être facilement connectées à des outils BI externes comme:</p>
                    <ul>
                        <li>Tableau</li>
                        <li>Power BI</li>
                        <li>Looker</li>
                        <li>Mode Analytics</li>
                    </ul>
                    <p>Utilisez les connecteurs Snowflake natifs disponibles dans ces plateformes.</p>
                </div>
            </div>
        </div>
    </div>
</section>

<section>
    <h2>Performance et optimisation</h2>
    
    <div class="alert alert-info">
        <strong>Conseil:</strong> Pour des volumes importants, considérez l'utilisation d'un cluster Kubernetes pour le déploiement d'Airflow.
    </div>
    
    <div class="row">
        <div class="col">
            <h3>Métriques clés</h3>
            <table>
                <thead>
                    <tr>
                        <th>Métrique</th>
                        <th>Valeur typique</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Vitesse d'extraction</td>
                        <td>~5-10 produits/minute</td>
                    </tr>
                    <tr>
                        <td>Consommation mémoire</td>
                        <td>200-500 MB</td>
                    </tr>
                    <tr>
                        <td>Taux de succès</td>
                        <td>95-98%</td>
                    </tr>
                    <tr>
                        <td>Débit réseau</td>
                        <td>~1-5 MB/s</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="col">
            <h3>Recommandations d'optimisation</h3>
            <ul>
                <li>Ajustez <code>travailleurs_max</code> selon les ressources disponibles</li>
                <li>Augmentez progressivement <code>requetes_par_seconde</code> pour trouver l'équilibre optimal</li>
                <li>Utilisez un pool de proxies de haute qualité</li>
                <li>Configurez une rotation d'agents utilisateurs diversifiée</li>
                <li>Implémentez le caching des requêtes pour réduire la charge</li>
            </ul>
        </div>
    </div>
</section>

<section>
    <h2>Extensions et développements futurs</h2>
    
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">Intégration NLP</div>
                <div class="card-body">
                    <p>Traitement avancé des avis clients par analyse de sentiment et extraction d'entités.</p>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">Surveillance des prix</div>
                <div class="card-body">
                    <p>Suivi historique et alertes sur les variations de prix pour les produits sélectionnés.</p>
                </div>
            </div>
        </div>
        
        <div class="col">
            <div class="card">
                <div class="card-header">API REST</div>
                <div class="card-body">
                    <p>Exposition des données via une API REST pour faciliter l'intégration avec d'autres systèmes.</p>
                </div>
            </div>
        </div>
    </div>
</section>

<div class="footer">
    <h3>Plateforme d'Extraction et d'Analyse de Produits Amazon</h3>
    <p>© 2025 - Tous droits réservés</p>
    <div style="margin-top: 10px;">
        <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">Documentation</a>
        <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">GitHub</a>
        <a href="#" style="color: white; text-decoration: none; margin: 0 10px;">Support</a>
    </div>
</div>

</body>
</html>
