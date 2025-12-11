import os
import sys
import boto3
import urllib3
from botocore.config import Config
from dotenv import load_dotenv

# Desativa avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CARREGAR AMBIENTE (.ENV) =================
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(DIRETORIO_ATUAL, '.env')
load_dotenv(dotenv_path)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

PASTA_FOTOS = os.path.join(DIRETORIO_ATUAL, "fotos")

# ================= IMPORTAÇÃO DE CONFIG_CLIENTES =================
if DIRETORIO_ATUAL not in sys.path:
    sys.path.append(DIRETORIO_ATUAL)

try:
    from src.config_clientes import CLIENTES
except ImportError:
    try:
        sys.path.append(os.path.join(DIRETORIO_ATUAL, 'src'))
        from config_clientes import CLIENTES
    except ImportError:
        CLIENTES = {}

def obter_cliente_s3():
    """Cria e retorna a conexão com o MinIO"""
    if not MINIO_ENDPOINT or not MINIO_ACCESS_KEY:
        print("[ERRO] Variáveis de ambiente não encontradas no .env")
        return None

    config = Config(
        connect_timeout=30, 
        read_timeout=120,   
        retries={'max_attempts': 3},
        signature_version='s3v4'
    )

    return boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=config,
        verify=False
    )

def obter_pasta_raiz_offs():
    if not CLIENTES:
        return "cx/compartilhado/offs"
    
    primeiro_caminho = list(CLIENTES.values())[0]
    caminho_relativo = primeiro_caminho
    if MINIO_BUCKET and primeiro_caminho.startswith(f"{MINIO_BUCKET}/"):
        caminho_relativo = primeiro_caminho[len(MINIO_BUCKET)+1:]
        
    if '/' in caminho_relativo:
        pasta_raiz = caminho_relativo.rsplit('/', 1)[0]
        return pasta_raiz
    
    return "cx/compartilhado/offs"

def limpar_pasta_remota(s3_client, bucket, prefixo_pasta):
    """
    Apaga arquivos um por um para evitar erro de MissingContentMD5 no MinIO.
    """
    print(f"   🧹 Limpando pasta remota: {prefixo_pasta} ...")
    
    try:
        # Lista objetos na pasta
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefixo_pasta)
        
        if 'Contents' in response:
            objetos = response['Contents']
            print(f"      Encontrados {len(objetos)} arquivos antigos. Apagando...")
            
            # Deleta um por um (Mais lento, porém compatível com qualquer S3/MinIO)
            for obj in objetos:
                try:
                    s3_client.delete_object(Bucket=bucket, Key=obj['Key'])
                    # print(f"         - Deletado: {obj['Key']}") # Descomente se quiser ver detalhado
                except Exception as e_del:
                    print(f"         ❌ Erro ao deletar {obj['Key']}: {e_del}")
            
            print("      ✅ Limpeza concluída.")
        else:
            print("      (Pasta já estava vazia ou não existia)")
            
    except Exception as e:
        print(f"      ⚠️ Erro ao listar/limpar pasta remota: {e}")

def executar_upload(nome_pasta_especifica=None):
    """
    Função principal.
    Se nome_pasta_especifica for passado, sobe APENAS essa pasta.
    Se for None, varre tudo em 'fotos'.
    """
    print("\n" + "="*50)
    print(f" 🚀 INICIANDO UPLOAD {'(Focado: ' + nome_pasta_especifica + ')' if nome_pasta_especifica else '(Geral)'}")
    print("="*50)
    
    if not os.path.exists(PASTA_FOTOS):
        print(f"[ERRO] A pasta local '{PASTA_FOTOS}' não existe.")
        return

    s3 = obter_cliente_s3()
    if not s3: return

    try:
        s3.list_objects_v2(Bucket=MINIO_BUCKET, MaxKeys=1) 
    except Exception as e:
        print(f"❌ Erro de conexão com MinIO: {e}")
        return

    pasta_raiz_remota = obter_pasta_raiz_offs()
    print(f"📂 Raiz Remota: {pasta_raiz_remota}")

    # Define quais pastas locais processar
    pastas_alvo = []
    if nome_pasta_especifica:
        caminho_esp = os.path.join(PASTA_FOTOS, nome_pasta_especifica)
        if os.path.isdir(caminho_esp):
            pastas_alvo = [nome_pasta_especifica]
        else:
            print(f"⚠️ A pasta específica '{nome_pasta_especifica}' não foi encontrada em 'fotos'.")
            return
    else:
        pastas_alvo = [d for d in os.listdir(PASTA_FOTOS) if os.path.isdir(os.path.join(PASTA_FOTOS, d))]

    # 1. LIMPEZA E UPLOAD POR PASTA
    sucessos = 0
    erros = 0

    for pasta in pastas_alvo:
        caminho_local_pasta = os.path.join(PASTA_FOTOS, pasta)
        caminho_remoto_pasta = f"{pasta_raiz_remota}/{pasta}/"
        
        # Limpa o destino específico desta pasta
        limpar_pasta_remota(s3, MINIO_BUCKET, caminho_remoto_pasta)
        
        # Sobe os arquivos DESTA pasta
        print(f"   📤 Enviando arquivos de: {pasta}")
        
        for root, dirs, files in os.walk(caminho_local_pasta):
            for file in files:
                if file.lower().endswith('.pdf'):
                    caminho_arquivo = os.path.join(root, file)
                    caminho_relativo = os.path.relpath(caminho_arquivo, PASTA_FOTOS)
                    caminho_relativo_s3 = caminho_relativo.replace(os.sep, '/')
                    
                    key_remota = f"{pasta_raiz_remota}/{caminho_relativo_s3}"
                    
                    print(f"      > {file} ... ", end="")
                    sys.stdout.flush()
                    
                    try:
                        with open(caminho_arquivo, "rb") as f:
                            s3.upload_fileobj(
                                f, 
                                MINIO_BUCKET, 
                                key_remota,
                                ExtraArgs={'ContentType': 'application/pdf'}
                            )
                        print("OK ✅")
                        sucessos += 1
                    except Exception as e:
                        print(f"ERRO ❌ ({e})")
                        erros += 1

    print("\n" + "="*40)
    print(f"UPLOAD FINALIZADO.")
    print(f"Sucessos: {sucessos}")
    print(f"Erros:    {erros}")
    print("="*40)

if __name__ == "__main__":
    executar_upload()
    input("Pressione Enter para fechar...")