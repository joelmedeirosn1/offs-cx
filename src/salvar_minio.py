# src/salvar_minio.py (versão final sem emojis)
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Carregar variáveis de ambiente do .env na raiz do projeto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Variáveis de configuração do MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_FOLDER = os.getenv("MINIO_FOLDER")

# A pasta de onde pegaremos as imagens é a 'fotos'
PASTA_FOTOS = "fotos"

def enviar_para_minio(nome_arquivo_local: str):
    """
    Envia um arquivo de imagem local para o MinIO no bucket e pasta configurados.
    """
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        )

        if not os.path.isfile(nome_arquivo_local):
            print(f"ERRO: Arquivo local nao encontrado: {nome_arquivo_local}")
            return

        remote_path = f"{MINIO_FOLDER}/{os.path.basename(nome_arquivo_local)}"
        
        content_type = 'image/jpeg' if nome_arquivo_local.lower().endswith(('.jpeg', '.jpg')) else 'image/png'
        extra_args = { 'ContentType': content_type }

        s3.upload_file(nome_arquivo_local, MINIO_BUCKET, remote_path, ExtraArgs=extra_args)
        # Linha corrigida - sem emoji
        print(f"INFO: Upload para MinIO concluido: {remote_path}")

    except NoCredentialsError:
        print("ERRO: Credenciais ausentes ao conectar com o MinIO. Verifique seu .env.")
    except ClientError as e:
        print(f"ERRO: Erro de cliente ao conectar com o MinIO: {e}")
    except Exception as e:
        # Linha corrigida - sem emoji
        print(f"ERRO: Erro inesperado ao enviar {nome_arquivo_local}: {e}")

def enviar_todas_as_imagens():
    """
    Envia todas as imagens da pasta 'fotos' para o MinIO.
    """
    caminho_raiz_projeto = os.path.join(os.path.dirname(__file__), '..')
    caminho_pasta_fotos = os.path.join(caminho_raiz_projeto, PASTA_FOTOS)

    if not os.path.isdir(caminho_pasta_fotos):
        print(f"AVISO: Pasta de origem nao encontrada: {caminho_pasta_fotos}")
        return

    imagens = [f for f in os.listdir(caminho_pasta_fotos) if f.lower().endswith((".jpeg", ".png", ".jpg"))]

    if not imagens:
        print("AVISO: Nenhuma imagem encontrada para envio na pasta 'fotos'.")
        return

    for imagem in imagens:
        caminho_completo = os.path.join(caminho_pasta_fotos, imagem)
        enviar_para_minio(caminho_completo)

if __name__ == "__main__":
    enviar_todas_as_imagens()