# amazon/docker/airflow/Dockerfile

# Utilisez une image officielle Airflow comme base
# Choisissez une version spécifique pour la reproductibilité, par exemple 2.9.2
# Vous pouvez trouver les tags disponibles sur Docker Hub: https://hub.docker.com/r/apache/airflow/tags
ARG AIRFLOW_VERSION=2.9.2
FROM apache/airflow:${AIRFLOW_VERSION}-python3.10

# Définir le répertoire de base d'Airflow
ENV AIRFLOW_HOME=/opt/airflow
# Ajouter les répertoires de nos modules personnalisés au PYTHONPATH
# Cela permettra à vos DAGs d'importer directement depuis 'scrapers' et 'utils'
ENV PYTHONPATH="${PYTHONPATH}:${AIRFLOW_HOME}/scrapers:${AIRFLOW_HOME}/utils"

# Passer à l'utilisateur root pour installer les paquets système
USER root

# Variables d'environnement pour éviter les questions interactives lors des installations
ENV DEBIAN_FRONTEND=noninteractive

# Installer les dépendances système nécessaires pour le scraping et Selenium
# - chromium et chromium-driver pour Selenium avec Chrome
# - libpq-dev pour psycopg2 (PostgreSQL)
# - default-libmysqlclient-dev pour mysql-connector-python (MySQL)
# - build-essential pour compiler certaines dépendances Python si nécessaire
# - curl et gnupg peuvent être utiles pour ajouter des dépôts ou clés
RUN apt-get update -yqq && \
    apt-get install -yqq --no-install-recommends \
    chromium \
    chromium-driver \
    libpq-dev \
    default-libmysqlclient-dev \
    build-essential \
    curl \
    gnupg && \
    # Nettoyage pour réduire la taille de l'image
    apt-get autoremove -yqq --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Revenir à l'utilisateur airflow pour les opérations suivantes
USER airflow

# Copier le fichier des dépendances Python (situé à la racine du projet ../../ par rapport à ce Dockerfile)
COPY --chown=airflow:airflow ../../requirements.txt /requirements.txt
# Installer les dépendances Python en tant qu'utilisateur airflow
# --user installe les paquets dans le répertoire home de l'utilisateur airflow (/home/airflow/.local)
# ce qui est une bonne pratique et évite les conflits de permissions.
# Le répertoire /home/airflow/.local/bin est généralement déjà dans le PATH.
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /requirements.txt

# Copier les modules de scraping et les utilitaires dans l'image
# Ils seront placés dans $AIRFLOW_HOME et ajoutés au PYTHONPATH (voir ENV PYTHONPATH ci-dessus)
COPY --chown=airflow:airflow ../../scrapers/ ${AIRFLOW_HOME}/scrapers/
COPY --chown=airflow:airflow ../../utils/ ${AIRFLOW_HOME}/utils/

# Copier la configuration Airflow personnalisée
# Ce fichier airflow.cfg sera utilisé par Airflow dans le conteneur.
COPY --chown=airflow:airflow ../../config/airflow.cfg ${AIRFLOW_HOME}/airflow.cfg

# Copier les DAGs dans l'image.
# Bien que ce dossier soit souvent monté en volume via docker-compose,
# le copier ici peut être utile pour des tests ou une utilisation autonome de l'image.
COPY --chown=airflow:airflow ../../airflow_dags/ ${AIRFLOW_HOME}/dags/

# Configurations pour Selenium
# Si vous utilisez un Selenium Grid distant, décommentez et configurez :
# ENV SELENIUM_GRID_URL="http://<votre_selenium_grid_host>:<port>/wd/hub"
# Pour le ChromeDriver local installé via apt-get :
# Il est généralement installé dans /usr/bin/chromedriver.
# Assurez-vous que /usr/bin est dans le PATH (l'image de base le fait souvent).
# Nous pouvons l'ajouter explicitement pour s'assurer qu'il est trouvé.
ENV PATH="${PATH}:/usr/bin:/home/airflow/.local/bin"

# Optimisations Airflow (exemples)
# Ces variables peuvent être définies ici, dans airflow.cfg, ou via docker-compose.yml.
# Préférez docker-compose.yml ou airflow.cfg pour une gestion plus flexible.
# ENV AIRFLOW__CORE__PARALLELISM=32
# ENV AIRFLOW__CORE__DAG_CONCURRENCY=16
# ENV AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC=5

# Le répertoire de travail par défaut est déjà ${AIRFLOW_HOME} dans l'image de base.
# WORKDIR ${AIRFLOW_HOME}

# Le port 8080 (webserver Airflow) est déjà exposé par l'image de base.
# EXPOSE 8080

# Le point d'entrée (ENTRYPOINT) et la commande par défaut (CMD) sont hérités
# de l'image de base apache/airflow. Ils s'occupent de l'initialisation
# de la base de données et du démarrage des services Airflow (scheduler, webserver, etc.).