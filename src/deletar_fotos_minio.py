# src/deletar_fotos_minio.py (versão final corrigida)
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
    Usa exclusão individual para contornar o erro MissingContentMD5 no MinIO.
    """
    if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_FOLDER]):
        print("ERRO: Variaveis de ambiente do MinIO nao estao configuradas corretamente.")
        return

    s3 = None
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        )

        # 1. Lista todos os objetos na pasta especificada
        response = s3.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=f"{MINIO_FOLDER}/")

        if 'Contents' not in response:
            print("AVISO: Nenhum arquivo encontrado no bucket para deletar.")
            return

        # 2. Prepara a lista de chaves (Keys) para deletar
        objetos_para_deletar_chaves = [obj['Key'] for obj in response['Contents']]
        
        print(f"INFO: Encontrado(s) {len(objetos_para_deletar_chaves)} arquivo(s) para deletar no MinIO.")

        # 3. DELETA OS OBJETOS INDIVIDUALMENTE (Correção para MissingContentMD5)
        for key in objetos_para_deletar_chaves:
            try:
                # Tenta deletar o objeto individualmente
                s3.delete_object(Bucket=MINIO_BUCKET, Key=key)
            except ClientError as e:
                # Se um único arquivo falhar, registra o erro e continua o loop
                print(f"AVISO: Falha ao deletar o objeto '{key}': {e}")
        
        print(f"INFO: Arquivos na pasta '{MINIO_FOLDER}' deletados com sucesso.")

    except ClientError as e:
        print(f"ERRO: Erro de cliente ao conectar com o MinIO: {e}")
    except Exception as e:
        print(f"ERRO: Erro inesperado ao deletar arquivos do MinIO: {e}")

if __name__ == "__main__":
    deletar_fotos_minio()