# src/deletar_fotos_minio.py (versão final corrigida, sem emojis)
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Carregar variáveis de ambiente do .env na raiz do projeto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Variáveis de configuração do MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_FOLDER = os.getenv("MINIO_FOLDER")

def deletar_fotos_minio():
    """
    Deleta todos os objetos na pasta configurada dentro do bucket do MinIO.
    """
    if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_FOLDER]):
        print("ERRO: Variaveis de ambiente do MinIO nao estao configuradas corretamente.")
        return

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        )

        # Lista todos os objetos na pasta especificada
        response = s3.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=f"{MINIO_FOLDER}/")

        if 'Contents' not in response:
            # Linha corrigida - sem emoji
            print("AVISO: Nenhum arquivo encontrado no bucket para deletar.")
            return

        # Prepara a lista de objetos para deletar
        objetos_para_deletar = [{'Key': obj['Key']} for obj in response['Contents']]
        
        print(f"INFO: Encontrado(s) {len(objetos_para_deletar)} arquivo(s) para deletar no MinIO.")

        # Deleta os objetos
        s3.delete_objects(Bucket=MINIO_BUCKET, Delete={'Objects': objetos_para_deletar})
        
        print(f"INFO: Arquivos na pasta '{MINIO_FOLDER}' deletados com sucesso.")

    except ClientError as e:
        # Linha corrigida - sem emoji
        print(f"ERRO: Erro de cliente ao conectar com o MinIO: {e}")
    except Exception as e:
        # Linha corrigida - sem emoji
        print(f"ERRO: Erro inesperado ao deletar arquivos do MinIO: {e}")

if __name__ == "__main__":
    deletar_fotos_minio()