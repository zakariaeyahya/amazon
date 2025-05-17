import boto3
import os

# Crée un client S3
s3 = boto3.client(
    's3',
    aws_access_key_id='AQQQQ',
    aws_secret_access_key='AXXX',
    region_name='eu-north-1'
)

bucket_name = 'electronique2025'
prefix = 'web-mining-data/'

# 📁 Dossier courant où tu as ton script
local_dir = os.path.dirname(os.path.abspath(__file__))

# Liste les objets S3
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
for obj in response.get('Contents', []):
    key = obj['Key']
    
    # Ignore les "dossiers" (ex. : juste web-mining-data/)
    if key.endswith('/'):
        continue

    file_name = key.split('/')[-1]
    local_path = os.path.join(local_dir, file_name)

    print(f"📥 Téléchargement de {key} vers {local_path}")
    s3.download_file(bucket_name, key, local_path)
    print(f"✅ {file_name} téléchargé.")
