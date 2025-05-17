import os
import boto3
import time
from pathlib import Path

def upload_files_to_s3(local_base_path, s3_bucket_name, s3_prefix=""):
    """
    Charge récursivement tous les fichiers CSV et JSON d'une structure de dossiers vers S3
    
    :param local_base_path: Chemin local de base (D:/bureau/BD&AI 1/ci2/S2/web_mining/comment/data)
    :param s3_bucket_name: Nom du bucket S3
    :param s3_prefix: Préfixe pour les objets S3 (dossier virtuel)
    """
    # Configuration AWS - remplacez avec vos propres identifiants
    s3_client = boto3.client(
        's3',
        aws_access_key_id='AKIAT3W73OPXZVPLYW6A',
        aws_secret_access_key='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',
        region_name='eu-north-1'
    )
    
    # Compteurs pour le suivi
    total_files = 0
    uploaded_files = 0
    
    # Vérifier que le chemin local existe
    if not os.path.exists(local_base_path):
        print(f"❌ Erreur: Le chemin {local_base_path} n'existe pas.")
        return
    
    # Fonction pour parcourir récursivement les dossiers
    def process_directory(current_path, relative_path=""):
        nonlocal total_files, uploaded_files
        
        print(f"Exploration du dossier: {current_path}")
        
        # Liste tous les éléments du dossier
        try:
            items = os.listdir(current_path)
        except PermissionError:
            print(f"❌ Erreur: Impossible d'accéder au dossier {current_path} (permission refusée)")
            return
        
        for item in items:
            item_path = os.path.join(current_path, item)
            
            # Si c'est un dossier, on explore récursivement
            if os.path.isdir(item_path):
                new_relative_path = os.path.join(relative_path, item)
                process_directory(item_path, new_relative_path)
                
            # Si c'est un fichier CSV ou JSON, on le télécharge
            elif item.lower().endswith(('.csv', '.json')):
                total_files += 1
                
                # Construire le chemin S3
                if s3_prefix:
                    s3_key = f"{s3_prefix}/{relative_path}/{item}"
                else:
                    s3_key = f"{relative_path}/{item}"
                
                # Normaliser le chemin pour S3 (utiliser des '/' au lieu de '\')
                s3_key = s3_key.replace('\\', '/')
                
                # Supprimer les doubles slashs et les slashs au début
                while '//' in s3_key:
                    s3_key = s3_key.replace('//', '/')
                if s3_key.startswith('/'):
                    s3_key = s3_key[1:]
                
                print(f"Téléchargement de {item_path} vers s3://{s3_bucket_name}/{s3_key}")
                
                try:
                    # Télécharger le fichier vers S3
                    s3_client.upload_file(
                        Filename=item_path,
                        Bucket=s3_bucket_name,
                        Key=s3_key
                    )
                    uploaded_files += 1
                    print(f"✅ Téléchargement réussi: {s3_key}")
                except Exception as e:
                    print(f"❌ Erreur lors du téléchargement de {item}: {str(e)}")
    
    # Démarrer le processus de téléchargement
    start_time = time.time()
    process_directory(local_base_path)
    end_time = time.time()
    
    # Afficher un résumé
    duration = end_time - start_time
    print("\n" + "="*50)
    print(f"Résumé du téléchargement:")
    print(f"Fichiers traités: {total_files}")
    print(f"Fichiers téléchargés avec succès: {uploaded_files}")
    print(f"Temps total: {duration:.2f} secondes")
    print("="*50)

if __name__ == "__main__":
    # Chemin local des données - modifié selon votre spécification
    local_data_path = r"D:\bureau\BD&AI 1\ci2\S2\web_mining\comment\data"
    
    # Configuration S3
    s3_bucket = "electronique2025"  # Bucket modifié selon votre spécification
    s3_folder = "web-mining-data"   # dossier virtuel dans S3
    
    # Lancer le téléchargement
    upload_files_to_s3(local_data_path, s3_bucket, s3_folder)