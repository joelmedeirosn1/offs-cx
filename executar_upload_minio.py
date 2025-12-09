import os
import sys
import boto3
import urllib3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config
from dotenv import load_dotenv

# Desativa avisos de segurança SSL (para servidores internos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CARREGAR AMBIENTE (.ENV) =================
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(DIRETORIO_ATUAL, '.env')
load_dotenv(dotenv_path)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# ================= CONFIGURAÇÃO DE PASTAS =================
PASTA_FOTOS = os.path.join(DIRETORIO_ATUAL, "fotos")

# Importa a lista de clientes para saber a pasta raiz
sys.path.append(DIRETORIO_ATUAL)
try:
    from src.config_clientes import CLIENTES
except ImportError:
    try:
        sys.path.append(os.path.join(DIRETORIO_ATUAL, 'src'))
        from config_clientes import CLIENTES
    except ImportError:
        print("[ERRO CRÍTICO] Não encontrei o arquivo 'config_clientes.py'.")
        sys.exit()

def obter_cliente_s3():
    """Cria e retorna a conexão com o MinIO"""
    if not MINIO_ENDPOINT or not MINIO_ACCESS_KEY:
        print("[ERRO] Variáveis de ambiente não encontradas no .env")
        sys.exit()

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
    """
    Descobre qual é a pasta geral onde os arquivos ficam (ex: compartilhado/offs).
    """
    if not CLIENTES:
        return None
    
    # Pega o primeiro caminho configurado
    primeiro_caminho = list(CLIENTES.values())[0]
    
    # Remove o nome do bucket do início se necessário
    caminho_relativo = primeiro_caminho
    if MINIO_BUCKET and primeiro_caminho.startswith(f"{MINIO_BUCKET}/"):
        caminho_relativo = primeiro_caminho[len(MINIO_BUCKET)+1:]
        
    # Pega o diretório pai (remove o nome do cliente final)
    if '/' in caminho_relativo:
        pasta_raiz = caminho_relativo.rsplit('/', 1)[0]
        return pasta_raiz
    
    return ""

def limpar_diretorio_geral(s3_client, bucket, prefixo):
    """
    Apaga TUDO (arquivos e subpastas) dentro do prefixo especificado.
    """
    print(f"\n--- 🧹 LIMPEZA GERAL REMOTA: '{prefixo}/' ---")
    
    if prefixo and not prefixo.endswith('/'):
        prefixo += '/'
    
    total_removido = 0
    
    while True:
        try:
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefixo)
            
            if 'Contents' not in response:
                if total_removido == 0:
                    print("   -> A pasta já está vazia.")
                break
                
            objetos = response['Contents']
            if not objetos:
                break
            
            print(f"   -> Apagando lote de {len(objetos)} itens...")
            
            for obj in objetos:
                try:
                    s3_client.delete_object(Bucket=bucket, Key=obj['Key'])
                    total_removido += 1
                except Exception as e_del:
                    print(f"      [ERRO] Falha ao apagar {obj['Key']}: {e_del}")

            if not response.get('IsTruncated'):
                break
                
        except Exception as e:
            print(f"   [ERRO CRÍTICO NA LIMPEZA]: {e}")
            break

    print(f"   ✅ Limpeza concluída. Total apagado: {total_removido}")

def enviar_arquivos():
    print("--- 🚀 INICIANDO UPLOAD DOS PDFs ---")
    
    if not os.path.exists(PASTA_FOTOS):
        print(f"[ERRO] A pasta '{PASTA_FOTOS}' não existe.")
        return

    arquivos = [f for f in os.listdir(PASTA_FOTOS) if f.lower().endswith('.pdf')]
    if not arquivos:
        print("[AVISO] Nenhum PDF encontrado na pasta local 'fotos'.")
        return

    print(f"📄 Arquivos locais encontrados: {len(arquivos)}")
    
    # 1. Conecta
    try:
        s3 = obter_cliente_s3()
        s3.list_objects_v2(Bucket=MINIO_BUCKET, MaxKeys=1) # Teste rápido
        print("✅ Conexão com MinIO OK.")
    except Exception as e:
        print(f"❌ Erro de conexão com MinIO: {e}")
        return

    # 2. Descobre pasta raiz e Limpa
    pasta_raiz = obter_pasta_raiz_offs()
    if pasta_raiz:
        limpar_diretorio_geral(s3, MINIO_BUCKET, pasta_raiz)
    else:
        print("[ERRO] Não foi possível determinar a pasta raiz 'offs' pelo config.")
        return

    # 3. Envia Arquivos
    print("\n--- 📤 ENVIANDO ARQUIVOS ---")
    sucessos = 0
    erros = 0

    for arquivo in arquivos:
        # Monta caminho remoto: compartilhado/offs/CLIENTE.pdf
        key_remota = f"{pasta_raiz}/{arquivo}"
        caminho_local = os.path.join(PASTA_FOTOS, arquivo)
        
        print(f"> {arquivo} ... ", end="")
        sys.stdout.flush()
        
        try:
            with open(caminho_local, "rb") as f:
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
    print(f"PROCESSO FINALIZADO.")
    print(f"Sucessos: {sucessos}")
    print(f"Erros:    {erros}")
    print("="*40)
    input("Pressione Enter para fechar...")

if __name__ == "__main__":
    enviar_arquivos()