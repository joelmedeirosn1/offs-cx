import time
import sys
import os
import glob
import math
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ================= CONFIGURAÇÃO DE DIMENSÃO E ESPERA =================
PADRAO_LARGURA = 1920
PADRAO_ALTURA = 1080 
WAIT_TIMEOUT = 10 

# ================= CONFIGURAÇÃO DE DATAS E PASTAS =================
data_hoje = datetime.now()
data_inicio = data_hoje - timedelta(days=7) 

nome_pasta_data = f"Relatorios_{data_inicio.strftime('%d-%m')}_a_{data_hoje.strftime('%d-%m')}"

PASTA_PERFIL_BOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perfil_bot")
PASTA_RAIZ_FOTOS = r"C:\Users\RT-121\Documents\RT\cx off-20251125T174423Z-1-001\cx off\fotos"
PASTA_FINAL = os.path.join(PASTA_RAIZ_FOTOS, nome_pasta_data) 

ALTURA_CORTE_BARRA_SUPERIOR = 80 
MARGEM_SUPERIOR_EXTRA = 100 

if not os.path.exists(PASTA_FINAL):
    os.makedirs(PASTA_FINAL)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config_clientes import CLIENTES, URL_RELATORIO

# ================= XPATHS MAPEADOS =================
XPATH_FILTRO = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[5]/ng2-canvas-component[1]/div[1]/div[1]/div[1]'
XPATH_PAGINACAO = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[3]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]/table-wrapper[1]/div[1]/ng2-table[1]/div[1]/div[6]/div[3]'
XPATH_SCROLL = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[3]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]/table-wrapper[1]/div[1]/ng2-table[1]/div[1]/div[3]/div[2]'

# === XPATHS DE DATA (Confirmados) ===
XPATH_CALENDARIO = "//mat-icon[contains(text(),'calendar')]/ancestor::div[1]"
XPATH_DROPDOWN = "//span[contains(text(), 'Fixo') or contains(text(), 'Automático') or contains(text(), 'Período')]"
XPATH_CATEGORIA = "//span[contains(text(), 'Últimos 7 dias')]"
XPATH_SUBMENU = "(//span[contains(text(), 'Últimos 7 dias')])[last()]"
XPATH_BTN_APLICAR = "//button[.//span[contains(text(), 'Aplicar')] or contains(text(), 'Aplicar')]"


def iniciar_navegador():
    print("--- Iniciando Robô ---")
    options = Options()
    options.add_argument(f"user-data-dir={PASTA_PERFIL_BOT}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(PADRAO_LARGURA, PADRAO_ALTURA)
    return driver

def limpar_pasta_fotos():
    print(f"--- Limpando pasta de fotos temporária: {PASTA_FINAL} ---")
    files = glob.glob(os.path.join(PASTA_FINAL, "*"))
    for f in files:
        try: os.remove(f)
        except: pass
    print("Pasta temporária limpa.\n")

def configurar_filtro_data(driver):
    """ Configura data e clica em Aplicar """
    print("\n⏰ Configurando DATA (Últimos 7 dias)...")
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. Calendário
        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_CALENDARIO)))
        driver.execute_script("arguments[0].click();", btn_cal)
        time.sleep(1.5)

        # 2. Dropdown
        btn_drop = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_DROPDOWN)))
        try: btn_drop.click()
        except: driver.execute_script("arguments[0].click();", btn_drop)
        time.sleep(1.5)

        # 3. Categoria "Últimos 7 dias"
        elementos_cat = driver.find_elements(By.XPATH, XPATH_CATEGORIA)
        clicou_cat = False
        for elem in elementos_cat:
            if elem.is_displayed():
                driver.execute_script("arguments[0].click();", elem)
                clicou_cat = True
                break
        if not clicou_cat: raise Exception("Categoria 'Últimos 7 dias' não encontrada.")
        time.sleep(1.5)

        # 4. Submenu Final
        submenu = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_SUBMENU)))
        driver.execute_script("arguments[0].click();", submenu)
        time.sleep(1)

        # 5. Botão Aplicar
        try:
            btn_aplicar = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_BTN_APLICAR)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_aplicar)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn_aplicar)
            print("   ✅ Botão 'Aplicar' clicado.")
        except TimeoutException:
            print("   ⚠️ Botão Aplicar não clicável, tentando ENTER.")
            ActionChains(driver).send_keys(Keys.ENTER).perform()
        
        time.sleep(6) 
        print("✅ Data configurada.")

    except Exception as e:
        print(f"❌ Erro Data: {e}")
        driver.save_screenshot(os.path.join(PASTA_FINAL, "DEBUG_ERRO_DATA.png"))

def ajustar_zoom(driver, nivel):
    try: driver.execute_script(f"document.body.style.zoom='{nivel}'")
    except: pass

def tentar_paginar(driver):
    try:
        botao_proximo = driver.find_element(By.XPATH, XPATH_PAGINACAO)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_proximo)
        classes = botao_proximo.get_attribute("class")
        aria_disabled = botao_proximo.get_attribute("aria-disabled")
        if "disabled" in str(classes) or aria_disabled == "true":
            return False 
        driver.execute_script("arguments[0].click();", botao_proximo)
        return True 
    except:
        return False

def criar_capa_personalizada(nome_cliente):
    print(f"   -> Gerando Capa...")
    width = PADRAO_LARGURA 
    height = 2715 
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    azul_cx = (0, 51, 102)
    preto = (0, 0, 0)
    cinza = (100, 100, 100)
    try:
        font_titulo = ImageFont.truetype("arial.ttf", 150)
        font_cliente = ImageFont.truetype("arial.ttf", 90)
        font_data = ImageFont.truetype("arial.ttf", 60)
    except:
        font_titulo = ImageFont.load_default()
        font_cliente = ImageFont.load_default()
        font_data = ImageFont.load_default()
    texto_titulo = "RELATÓRIO DE RUPTURA"
    texto_cliente = f"CLIENTE: {nome_cliente}"
    periodo_str = f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_hoje.strftime('%d/%m/%Y')}"
    gerado_em = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    def desenhar_centralizado(texto, fonte, y, cor):
        try:
            bbox = draw.textbbox((0, 0), texto, font=fonte)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = draw.textlength(texto, font=fonte)
        x = (width - text_width) / 2
        draw.text((x, y), texto, font=fonte, fill=cor)
    desenhar_centralizado(texto_titulo, font_titulo, 700, azul_cx)
    desenhar_centralizado(texto_cliente, font_cliente, 1000, preto)
    desenhar_centralizado(periodo_str, font_data, 1300, cinza)
    desenhar_centralizado(gerado_em, font_data, 1400, cinza)
    nome_arquivo = f"{nome_cliente}_00_CAPA.png".replace("/", "-")
    caminho_capa = os.path.join(PASTA_FINAL, nome_arquivo)
    img.save(caminho_capa)
    return caminho_capa

def salvar_print_tratado(driver, caminho_img):
    driver.save_screenshot(caminho_img)
    img = Image.open(caminho_img)
    width, height = img.size
    corte_box = (0, ALTURA_CORTE_BARRA_SUPERIOR, width, height)
    img_cortada = img.crop(corte_box)
    cor_fundo = img_cortada.getpixel((0, 0))
    largura_c, altura_c = img_cortada.size
    nova_altura = altura_c + MARGEM_SUPERIOR_EXTRA
    nova_imagem = Image.new("RGB", (largura_c, nova_altura), cor_fundo)
    nova_imagem.paste(img_cortada, (0, MARGEM_SUPERIOR_EXTRA))
    nova_imagem.save(caminho_img)
    img.close()

def capturar_com_scroll_inteligente(driver, nome_base, pagina_atual, lista_imagens):
    try:
        tabela_scroll = driver.find_element(By.XPATH, XPATH_SCROLL)
        altura_total = driver.execute_script("return arguments[0].scrollHeight", tabela_scroll)
        altura_visivel = driver.execute_script("return arguments[0].clientHeight", tabela_scroll)
        if altura_total <= altura_visivel:
            nome_arquivo = f"{nome_base}_pag{pagina_atual}.png"
            caminho_img = os.path.join(PASTA_FINAL, nome_arquivo)
            salvar_print_tratado(driver, caminho_img)
            lista_imagens.append(caminho_img)
            print(f"   -> Pag {pagina_atual}: Captura única.")
            return
        print(f"   -> Pag {pagina_atual}: Tabela longa. Iniciando scroll...")
        posicao_atual = 0
        parte = 1
        driver.execute_script("arguments[0].scrollTop = 0", tabela_scroll)
        time.sleep(1)
        while True:
            nome_arquivo = f"{nome_base}_pag{pagina_atual}_parte{parte:02d}.png"
            caminho_img = os.path.join(PASTA_FINAL, nome_arquivo)
            salvar_print_tratado(driver, caminho_img)
            lista_imagens.append(caminho_img)
            print(f"      Parte {parte} capturada.")
            if posicao_atual + altura_visivel >= altura_total: break
            step = altura_visivel - 100
            posicao_atual += step
            if posicao_atual > altura_total: posicao_atual = altura_total
            driver.execute_script(f"arguments[0].scrollTop = {posicao_atual}", tabela_scroll)
            time.sleep(2)
            parte += 1
    except Exception as e:
        print(f"   [Erro Scroll]: {e}")
        nome_erro = f"{nome_base}_pag{pagina_atual}_ERRO.png"
        caminho_erro = os.path.join(PASTA_FINAL, nome_erro)
        salvar_print_tratado(driver, caminho_erro)
        lista_imagens.append(caminho_erro)

def gerar_pdf_cliente(nome_cliente, lista_imagens):
    if not lista_imagens: return
    print(f"   -> Gerando PDF ({len(lista_imagens)} pág)...")
    try:
        img_inicial = Image.open(lista_imagens[0])
        if img_inicial.mode == 'RGBA': img_inicial = img_inicial.convert('RGB')
        imagens_restantes = []
        for caminho in lista_imagens[1:]:
            img = Image.open(caminho)
            if img.mode == 'RGBA': img = img.convert('RGB')
            imagens_restantes.append(img)
        nome_pdf = f"{nome_cliente}.pdf".replace("/", "-")
        caminho_pdf = os.path.join(PASTA_FINAL, nome_pdf)
        img_inicial.save(caminho_pdf, save_all=True, append_images=imagens_restantes)
        print(f"   [SUCESSO] PDF Criado: {caminho_pdf}")
        img_inicial.close()
        for img in imagens_restantes: img.close()
        for caminho in lista_imagens:
            try: os.remove(caminho)
            except: pass
    except Exception as e:
        print(f"   [ERRO PDF]: {e}")

def processar_relatorio():
    limpar_pasta_fotos() 
    driver = iniciar_navegador()
    driver.get(URL_RELATORIO)
    ajustar_zoom(driver, "100%")
    print("\n" + "="*50)
    print(" ROBÔ DE RELATÓRIOS SEMANAIS (DATA FIXA + FILTRO INTELIGENTE)")
    print(f" Pasta de Saída: {PASTA_FINAL}")
    print("="*50)
    input(">>> Quando carregado, APERTE ENTER <<<")

    # 1. DATA (Apenas uma vez)
    configurar_filtro_data(driver)

    wait = WebDriverWait(driver, 20)
    wait_curto = WebDriverWait(driver, 4) # Espera curta para pular cliente vazio
    actions = ActionChains(driver)

    for nome_cliente, pasta_minio in CLIENTES.items():
        print(f"\n------------------------------------------------")
        print(f"Processando: {nome_cliente}")
        ajustar_zoom(driver, "100%")
        imagens_deste_cliente = []
        
        try:
            # === FILTRAGEM DE CLIENTE ===
            print("1. Filtrando Cliente...")
            botao_filtro = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_FILTRO)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_filtro)
            time.sleep(1)
            
            # Clica no filtro (abre o menu)
            try: botao_filtro.click()
            except: driver.execute_script("arguments[0].click();", botao_filtro)
            time.sleep(1.5)

            # === DIGITA O NOME DO CLIENTE ===
            # Revertido para o método original que funcionava (input[type='text'])
            try:
                # Procura a caixa de texto padrão visível
                caixa = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                caixa.click()
                time.sleep(0.5)
                # Limpa campo
                caixa.send_keys(Keys.CONTROL + "a")
                caixa.send_keys(Keys.DELETE)
                time.sleep(0.5)
                
                print(f"   -> Digitando: {nome_cliente}")
                caixa.send_keys(nome_cliente)
                time.sleep(2.5) # Espera filtrar
            except:
                # Fallback: Tenta enviar teclas diretamente para o foco (funciona muitas vezes)
                print("   -> Input não encontrado. Tentando digitação direta...")
                actions.send_keys(nome_cliente).perform()
                time.sleep(2.5)

            # === SELEÇÃO "SOMENTE" / VERIFICAÇÃO SE EXISTE ===
            try:
                # Tenta encontrar o item na lista. Se não achar em 4s, assume que não tem dados.
                item_xpath = f"//div[@role='option' or contains(@class, 'item')]//*[contains(text(), '{nome_cliente}')]"
                item = wait_curto.until(EC.visibility_of_element_located((By.XPATH, item_xpath)))
                
                # Move o mouse para cima para aparecer o botão "Somente"
                actions.move_to_element(item).perform()
                time.sleep(0.5)

                # Tenta clicar em "Somente" (Isso limpa o filtro anterior!)
                clicou_somente = False
                try:
                    btn_somente = driver.find_element(By.XPATH, "//span[contains(text(), 'Somente') or contains(text(), 'Only') or contains(text(), 'somente')]")
                    if btn_somente.is_displayed():
                        driver.execute_script("arguments[0].click();", btn_somente)
                        print("   -> Clicou em 'Somente'.")
                        clicou_somente = True
                except:
                    pass

                if not clicou_somente:
                    print("   -> Botão 'Somente' não apareceu. Clicando no item...")
                    item.click()
                    # Se clicou no item, as vezes ele não fecha o menu sozinho ou não limpa o filtro anterior.
                    # Mas é o melhor fallback possível.
                
                # Fecha o menu (ESC)
                time.sleep(1)
                actions.send_keys(Keys.ESCAPE).perform()
                try: driver.find_element(By.TAG_NAME, "header").click()
                except: pass

            except TimeoutException:
                # === CLIENTE NÃO ENCONTRADO ===
                print(f"   ⚠️ CLIENTE '{nome_cliente}' NÃO ENCONTRADO na lista.")
                print("   -> Pulando...")
                
                # Fecha o menu que ficou aberto
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                try: driver.find_element(By.TAG_NAME, "body").click()
                except: pass
                
                continue # Pula para o próximo loop

            # === PROSSEGUE SE O CLIENTE EXISTE ===
            print("2. Aguardando dados (8s)...")
            time.sleep(8)

            # Gera Capa
            nome_limpo = nome_cliente.replace("/", "-").replace("\\", "-")
            caminho_capa = criar_capa_personalizada(nome_limpo)
            if caminho_capa: imagens_deste_cliente.append(caminho_capa)

            # Captura
            print("3. Capturando...")
            ajustar_zoom(driver, "60%")
            time.sleep(2)
            pagina_atual = 1
            while True:
                capturar_com_scroll_inteligente(driver, nome_limpo, pagina_atual, imagens_deste_cliente)
                if tentar_paginar(driver):
                    print("   -> Próxima página...")
                    time.sleep(5) 
                    pagina_atual += 1
                else:
                    print("   -> Fim da tabela.")
                    break
            
            ajustar_zoom(driver, "100%")
            gerar_pdf_cliente(nome_limpo, imagens_deste_cliente)
            
        except Exception as e:
            print(f"   [ERRO GERAL NO LOOP]: {e}")
            ajustar_zoom(driver, "100%")
            try: actions.send_keys(Keys.ESCAPE).perform()
            except: pass
            continue

    print("\n--- Finalizado ---")
    print(f"Arquivos salvos em: {PASTA_FINAL}")
    input("Enter para fechar...")
    driver.quit()

if __name__ == "__main__":
    processar_relatorio()