import snowflake.connector 
conn = snowflake.connector.connect(
        user='VGVDdc',
        password='XGFXXX',
        account='ZWW',
        role='XXXXQ'
    )


# Création du curseur
cur = conn.cursor()

# Test : requête simple
try:
    print("✅ Connexion réussie !\n")

    # Afficher l'utilisateur et la date
    cur.execute("SELECT CURRENT_USER(), CURRENT_DATE;")
    for row in cur:
        print("Utilisateur :", row[0])
        print("Date :", row[1])

    # Afficher les bases de données disponibles
    print("\n📂 Bases de données disponibles :")
    cur.execute("SHOW DATABASES;")
    for row in cur:
        print("-", row[1])  # row[1] = nom de la base
finally:
    cur.close()
    conn.close()
