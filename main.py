import time
import sys
import requests # Requer: pip install requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Configurações e Utilitários
import src.config as cfg
import gerador_relatorio_vazio
import upload_minio

# Classes do Robô
from src.bot_driver import BotDriver
from src.relatorio_nav import RelatorioNav
from src.pdf_manager import PDFManager

# Importa clientes do src
try:
    from src.config_clientes import CLIENTES
except ImportError:
    print("❌ Erro: CLIENTES não encontrado.")
    CLIENTES = {}

def acionar_n8n():
    """ Envia um sinal para o N8N iniciar o fluxo """
    if not cfg.N8N_WEBHOOK_URL or "seu-n8n" in cfg.N8N_WEBHOOK_URL:
        print("\n⚠️ URL do Webhook não configurada em src/config.py. N8N não será chamado.")
        return

    print(f"\n📞 Chamando N8N...")
    try:
        # Envia dados úteis para o N8N, como o nome da pasta que acabou de ser criada
        payload = {
            "pasta_relatorio": cfg.nome_pasta_data, 
            "data_filtro": cfg.texto_periodo_filtro,
            "status": "concluido"
        }
        
        response = requests.post(cfg.N8N_WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            print("✅ N8N acionado com sucesso!")
        else:
            print(f"⚠️ N8N retornou erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Falha ao chamar N8N: {e}")

def processar_relatorio():
    # 1. Inicialização
    bot = BotDriver()
    nav = RelatorioNav(bot)
    pdf_mgr = PDFManager(bot)
    
    pdf_mgr.limpar_pasta_temporaria()
    
    print("   -> Acessando Looker Studio...")
    # URL default ou do config
    bot.get(getattr(cfg, 'URL_RELATORIO', "https://lookerstudio.google.com/u/0/reporting/ada033a0-55d4-4d59-981e-d65bd7e1a581/page/8gyPF"))
    
    print("\n" + "="*50)
    print(" 🤖 ROBÔ DE RELATÓRIOS (AUTOMÁTICO)")
    print(f" 📂 Saída: {cfg.PASTA_FINAL}")
    print(f" 📅 Data: {cfg.texto_periodo_filtro} ({cfg.label_periodo})")
    print("="*50)
    
    # Aguarda carregamento inicial e possível login automático por cookie
    print("⏳ Aguardando carregamento (20s)...")
    time.sleep(20)
    
    bot.ajustar_zoom("100%")

    # 2. Configurações Globais (Data e Justificativas)
    nav.configurar_data()
    sucesso_filtros = nav.configurar_justificativas()

    # 3. Lógica Principal
    if not sucesso_filtros:
        print("\n⚠️ Nenhuma justificativa encontrada. Gerando VAZIO para todos.")
        for nome_cliente in CLIENTES:
            print(f"   -> Gerando Vazio: {nome_cliente}")
            nome_limpo = nome_cliente.replace("/", "-").replace("\\", "-")
            gerador_relatorio_vazio.criar_relatorio_vazio(
                nome_limpo, cfg.texto_periodo_filtro, cfg.PASTA_FINAL, cfg.PASTA_DIR
            )
    else:
        # Loop por Cliente (Fluxo Normal)
        for nome_cliente in CLIENTES:
            print(f"\n------------------------------------------------")
            print(f"Processando: {nome_cliente}")
            bot.ajustar_zoom("100%")
            imagens_cliente = []

            try:
                # Tenta Filtrar Cliente
                nav.filtrar_cliente(nome_cliente)
                
                # Sucesso: Fecha menus e Captura
                nav.fechar_menus()
                print("2. Aguardando dados (8s)...")
                time.sleep(8)

                # Capa
                nome_limpo = nome_cliente.replace("/", "-").replace("\\", "-")
                capa = pdf_mgr.criar_capa(nome_limpo)
                if capa: imagens_cliente.append(capa)

                # Captura Tabela
                print("3. Capturando...")
                bot.ajustar_zoom("60%")
                time.sleep(2)
                
                pag = 1
                while True:
                    pdf_mgr.capturar_scroll(nome_limpo, pag, imagens_cliente)
                    if pdf_mgr.tentar_paginar():
                        print("   -> Próxima página...")
                        time.sleep(5)
                        pag += 1
                    else:
                        print("   -> Fim da tabela.")
                        break
                
                bot.ajustar_zoom("100%")
                pdf_mgr.gerar_pdf(nome_limpo, imagens_cliente)

            except TimeoutException:
                # Cliente não encontrado na lista -> Gera Vazio Fabricado
                print(f"   ⚠️ Cliente '{nome_cliente}' não encontrado. Gerando vazio...")
                
                ActionChains(bot.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                
                nome_limpo = nome_cliente.replace("/", "-").replace("\\", "-")
                gerador_relatorio_vazio.criar_relatorio_vazio(
                    nome_limpo, cfg.texto_periodo_filtro, cfg.PASTA_FINAL, cfg.PASTA_DIR
                )
                continue
                
            except Exception as e:
                print(f"   [ERRO LOOP]: {e}")
                bot.ajustar_zoom("100%")
                ActionChains(bot.driver).send_keys(Keys.ESCAPE).perform()
                continue

    # 4. Finalização
    bot.quit()
    
    # Upload da pasta do dia
    upload_minio.executar_upload(cfg.nome_pasta_data)
    
    # Chama o N8N para começar o envio
    acionar_n8n()

    print("\n--- Processo Finalizado ---")
    # input("Enter para sair...") # Removido para fechar sozinho em automação

if __name__ == "__main__":
    processar_relatorio()