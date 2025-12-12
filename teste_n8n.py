import requests
import sys
import os

# Adiciona o diretório atual ao path para importar configs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import src.config as cfg
except ImportError:
    print("❌ Erro: Não foi possível importar src.config. Verifique se o arquivo existe.")
    sys.exit()

def testar_conexao_n8n():
    print("\n" + "="*50)
    print(" 📡 TESTE DE CONEXÃO COM N8N")
    print("="*50)

    url = getattr(cfg, 'N8N_WEBHOOK_URL', None)
    
    if not url:
        print("❌ ERRO: Nenhuma URL configurada em 'src/config.py'.")
        print("   -> Adicione: N8N_WEBHOOK_URL = 'sua-url-aqui'")
        return

    print(f"URL Alvo: {url}")
    print("\n⚠️ IMPORTANTE: Se esta for uma URL de teste (webhook-test),")
    print("   certifique-se de ter clicado em 'Listen for Test Event' no n8n AGORA.")
    
    input(">>> Pressione ENTER para enviar o sinal de teste <<<")

    # Dados simulados iguais aos que o robô envia
    payload = {
        "pasta_relatorio": cfg.nome_pasta_data,
        "data_filtro": cfg.texto_periodo_filtro,
        "status": "teste_manual",
        "mensagem": "Este é um teste de acionamento manual via Python"
    }

    try:
        print(f"   -> Enviando POST...")
        response = requests.post(url, json=payload)
        
        print(f"   -> Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✅ SUCESSO! O N8N recebeu o sinal.")
            print(f"   Resposta do servidor: {response.text}")
        else:
            print(f"\n❌ FALHA. O N8N rejeitou o sinal.")
            print(f"   Mensagem de erro: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Erro crítico ao tentar conectar: {e}")

if __name__ == "__main__":
    testar_conexao_n8n()