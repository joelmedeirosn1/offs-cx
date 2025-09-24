import boto3
from botocore.exceptions import NoCredentialsError, ClientError

MINIO_ENDPOINT = "https://s3.rt-automations.com.br"
MINIO_ACCESS_KEY = "WhDvrzZfezGRPV6qm9Oc"
MINIO_SECRET_KEY = "vw5KKrgweBI0e71nWlWqPjloJRAXEnjK02WX93ju"
MINIO_BUCKET = "involves"
MINIO_FOLDER = "compartilhado/aderencia"

# Cria cliente boto3 compatível com MinIO
client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY
)

def enviar_para_minio(bucket, caminho_local, nome_arquivo):
    remote_path = f"{MINIO_FOLDER}/{nome_arquivo}"
    try:
        client.upload_file(
            caminho_local,
            bucket,
            remote_path,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
        print(f"🟢 Upload OK: {remote_path}")
    except NoCredentialsError:
        print("❌ Erro: Credenciais ausentes")
    except ClientError as e:
        print(f"❌ Erro de cliente MinIO: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar {nome_arquivo}: {e}")
