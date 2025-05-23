-- 1. Choix de la base et du schéma
USE DATABASE DATA;
USE SCHEMA PUBLIC;

-- 2. Création des tables

CREATE OR REPLACE TABLE product_info1 (
    asin STRING,
    manufacturer STRING,
    processor_type STRING,
    hard_drive_size STRING,
    hard_disk_description STRING,
    ram_size STRING,
    url STRING
);

CREATE OR REPLACE TABLE product_info2 (
    asin STRING,
    nombre_avis STRING,
    prix STRING,
    page STRING,
    note STRING,
    url STRING,
    titre STRING
);

CREATE OR REPLACE TABLE review (
    asin STRING,
    sentiment STRING
);

CREATE OR REPLACE TABLE classe_prix (
    classe STRING,
    prix_min FLOAT,
    prix_max FLOAT
);

-- 3. Création du stage pour charger les fichiers CSV

CREATE OR REPLACE STAGE DATA.PUBLIC.MON_STAGE
  FILE_FORMAT = (
    TYPE = 'CSV',
    FIELD_OPTIONALLY_ENCLOSED_BY = '"',
    SKIP_HEADER = 1
  );


-- 4. Chargement des fichiers CSV dans le stage


PUT file://pathtoproductinfotech1_cleaned.csv @DATA.PUBLIC.MON_STAGE;
PUT file://pathtoproductinfotech2_cleaned.csv @DATA.PUBLIC.MON_STAGE;
PUT file://pathtosentiments_par_asin.csv @DATA.PUBLIC.MON_STAGE;

-- Vérifier les fichiers dans le stage
LIST @DATA.PUBLIC.MON_STAGE;

-- 5. Chargement des données dans les tables depuis le stage

COPY INTO product_info1
FROM @DATA.PUBLIC.MON_STAGE/productinfotech1_cleaned.csv
FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);

COPY INTO product_info2
FROM @DATA.PUBLIC.MON_STAGE/productinfotech2_cleaned.csv
FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);

COPY INTO review
FROM @DATA.PUBLIC.MON_STAGE/sentiments_par_asin.csv
FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);

-- Vérification rapide
SELECT * FROM review LIMIT 10;

-- 6. Construction de la table full_product_info avec jointures
CREATE OR REPLACE TABLE full_product_info AS
SELECT 
    p1.asin,
    p1.manufacturer,
    p1.processor_type,
    p1.hard_drive_size,
    p1.hard_disk_description,
    p1.ram_size,
    p1.url AS url_info1,

    p2.nombre_avis,
    p2.prix,
    p2.page,
    p2.note,
    p2.url AS url_info2,
    p2.titre,

    r.sentiment

FROM product_info1 p1
JOIN product_info2 p2 ON p1.asin = p2.asin
JOIN review r ON p1.asin = r.asin;


-- 7. Nettoyage / transformation des données
-- Ajout d'une colonne hard_drive_size convertie en GB
ALTER TABLE full_product_info ADD COLUMN HARD_DRIVE_SIZE_IN_GB STRING;

UPDATE full_product_info
SET HARD_DRIVE_SIZE_IN_GB = CASE
    WHEN UPPER(hard_drive_size) LIKE '%TB%' THEN
        CAST(SUBSTRING(hard_drive_size, 1, LENGTH(hard_drive_size) - 2) AS FLOAT) * 1000 || ' GB'
    WHEN UPPER(hard_drive_size) LIKE '%GB%' THEN
        CAST(SUBSTRING(hard_drive_size, 1, LENGTH(hard_drive_size) - 2) AS FLOAT) || ' GB'
    ELSE NULL
END;

-- Suppression de l'ancienne colonne et renommage
ALTER TABLE full_product_info DROP COLUMN hard_drive_size;
ALTER TABLE full_product_info RENAME COLUMN HARD_DRIVE_SIZE_IN_GB TO hard_drive_size;

-- Correction des valeurs mal orthographiées dans processor_type
UPDATE full_product_info
SET processor_type = 'Autres'
WHERE processor_type ILIKE 'Aures';


-- 8. Création de la table de classification de prix


INSERT INTO classe_prix (classe, prix_min, prix_max) VALUES
('Bas', 0, 500),
('Moyen', 500.01, 1500),
('Élevé', 1500.01, 1000000);

-- 9. Création de la table full_product_info_classe avec la classe prix jointe

CREATE OR REPLACE TABLE full_product_info_classe AS
SELECT
    f.*,
    c.classe
FROM
    full_product_info f
LEFT JOIN
    classe_prix c
ON
    TO_NUMBER(REPLACE(REPLACE(f.prix, '£', ''), ',', '')) BETWEEN c.prix_min AND c.prix_max;

-- Vérification
SELECT * FROM full_product_info_classe ;
