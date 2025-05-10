import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='AKIAXXXXXXXX',
    aws_secret_access_key='abcdeXXXXXXXXX',
    region_name='eu-north-1'
)

response = s3.list_objects_v2(Bucket='electronique2025', Prefix='web-mining-data/')
for obj in response.get('Contents', []):
    print(obj['Key'])
