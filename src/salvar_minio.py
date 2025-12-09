import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Carregar variáveis de ambiente
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configurações fixas do MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
# A pasta padrão continua vindo do .env, caso não seja informada outra
MINIO_FOLDER_PADRAO = os.getenv("MINIO_FOLDER")

def get_minio_client():
    return boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )

def enviar_arquivo(caminho_local, pasta_destino=None):
    """
    Envia um arquivo local para o MinIO.
    :param caminho_local: Caminho do arquivo no PC.
    :param pasta_destino: (Opcional) Pasta no MinIO. Se não informado, usa a do .env.
    """
    if not pasta_destino:
        pasta_destino = MINIO_FOLDER_PADRAO

    if not os.path.isfile(caminho_local):
        print(f"ERRO: Arquivo não encontrado: {caminho_local}")
        return False

    nome_arquivo = os.path.basename(caminho_local)
    remote_path = f"{pasta_destino}/{nome_arquivo}" # Caminho final na nuvem

    client = get_minio_client()
    
    try:
        content_type = 'image/jpeg'
        if nome_arquivo.lower().endswith('.png'):
            content_type = 'image/png'
        elif nome_arquivo.lower().endswith('.pdf'):
            content_type = 'application/pdf'

        client.upload_file(
            caminho_local,
            MINIO_BUCKET,
            remote_path,
            ExtraArgs={'ContentType': content_type}
        )
        print(f"✅ Upload Sucesso: {nome_arquivo} -> {remote_path}")
        return True

    except Exception as e:
        print(f"❌ Erro no upload de {nome_arquivo}: {e}")
        return False