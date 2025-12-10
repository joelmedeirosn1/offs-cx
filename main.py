import time
import sys
import os
import glob
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

# ================= CÁLCULO DE DATAS (Texto da Capa) =================
hoje = datetime.now()
segunda_desta_semana = hoje - timedelta(days=hoje.weekday())
segunda_passada = segunda_desta_semana - timedelta(days=7)
domingo_passado = segunda_passada + timedelta(days=6)

str_data_inicio = segunda_passada.strftime('%d/%m/%Y')
str_data_fim = domingo_passado.strftime('%d/%m/%Y')

nome_pasta_data = f"Relatorios_{segunda_passada.strftime('%d-%m')}_a_{domingo_passado.strftime('%d-%m')}"

# ================= CONFIGURAÇÃO DE PASTAS =================
PASTA_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_PERFIL_BOT = os.path.join(PASTA_DIR, "perfil_bot")
PASTA_RAIZ_FOTOS = r"C:\Users\RT-121\Documents\RT\cx off-20251125T174423Z-1-001\cx off\fotos"
PASTA_FINAL = os.path.join(PASTA_RAIZ_FOTOS, nome_pasta_data) 

ALTURA_CORTE_BARRA_SUPERIOR = 80 
MARGEM_SUPERIOR_EXTRA = 100 

if not os.path.exists(PASTA_FINAL):
    os.makedirs(PASTA_FINAL)

sys.path.append(PASTA_DIR)
from src.config_clientes import CLIENTES, URL_RELATORIO

# ================= XPATHS MAPEADOS =================
XPATH_FILTRO = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[5]/ng2-canvas-component[1]/div[1]/div[1]/div[1]'
XPATH_PAGINACAO = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[3]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]/table-wrapper[1]/div[1]/ng2-table[1]/div[1]/div[6]/div[3]'
XPATH_SCROLL = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[3]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]/table-wrapper[1]/div[1]/ng2-table[1]/div[1]/div[3]/div[2]'

# === XPATHS DE DATA ===
XPATH_CALENDARIO = "//mat-icon[contains(text(),'calendar')]/ancestor::div[1]"
XPATH_DROPDOWN = "//span[contains(text(), 'Fixo') or contains(text(), 'Automático') or contains(text(), 'Período') or contains(text(), 'Últimos') or contains(text(), 'Semana')]"
XPATH_CATEGORIA_PAI = "//span[contains(text(), 'Últimos 7 dias')]" 
XPATH_OPCAO_SEMANA = "//span[contains(text(), 'Semana passada (começa na segunda-feira)')]"
XPATH_BTN_APLICAR = "//button[.//span[contains(text(), 'Aplicar')] or contains(text(), 'Aplicar')]"


def iniciar_navegador():
    print("--- Iniciando Robô ---")
    options = Options()
    options.add_argument(f"user-data-dir={PASTA_PERFIL_BOT}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3") 
    options.add_argument("--silent")
    
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
    """ Seleciona: Últimos 7 dias -> Semana passada (começa na segunda-feira) """
    print(f"\n⏰ Configurando DATA: Semana passada (Seg-Dom)...")
    wait = WebDriverWait(driver, 20)
    
    try:
        btn_cal = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_CALENDARIO)))
        driver.execute_script("arguments[0].click();", btn_cal)
        time.sleep(1.5)

        btn_drop = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_DROPDOWN)))
        try: btn_drop.click()
        except: driver.execute_script("arguments[0].click();", btn_drop)
        time.sleep(1.5)

        try:
            categorias = driver.find_elements(By.XPATH, XPATH_CATEGORIA_PAI)
            cat_pai = None
            for cat in reversed(categorias):
                if cat.is_displayed():
                    cat_pai = cat
                    break
            if cat_pai:
                driver.execute_script("arguments[0].click();", cat_pai)
                time.sleep(1)
        except: pass

        opcao_semana = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_OPCAO_SEMANA)))
        driver.execute_script("arguments[0].click();", opcao_semana)
        time.sleep(1.5)

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
        print("✅ Filtro de data aplicado.")

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
    print(f"   -> Gerando Capa (Paisagem + Logo)...")
    width = PADRAO_LARGURA 
    height = PADRAO_ALTURA 
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    azul_cx = (0, 51, 102)
    preto = (0, 0, 0)
    cinza = (100, 100, 100)

    # --- LOGO ---
    top_margin_logo = 80
    logo_height = 0
    possiveis_logos = ["cxtrade_logo.jpg", "logo_cx.png", "logo_cx.jpg"]
    caminho_logo = None
    
    for nome in possiveis_logos:
        temp_path = os.path.join(PASTA_DIR, nome)
        if os.path.exists(temp_path):
            caminho_logo = temp_path
            break
            
    try:
        if caminho_logo:
            logo_img = Image.open(caminho_logo)
            base_width = 400
            w_percent = (base_width / float(logo_img.size[0]))
            h_size = int((float(logo_img.size[1]) * float(w_percent)))
            logo_img = logo_img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            logo_x = int((width - base_width) / 2)
            logo_y = top_margin_logo
            
            if logo_img.mode == 'RGBA':
                 img.paste(logo_img, (logo_x, logo_y), logo_img)
            else:
                 img.paste(logo_img, (logo_x, logo_y))
            logo_height = h_size
    except: pass

    try:
        font_titulo = ImageFont.truetype("arial.ttf", 110) 
        font_cliente = ImageFont.truetype("arial.ttf", 80)  
        font_data = ImageFont.truetype("arial.ttf", 50)  
    except:
        font_titulo = ImageFont.load_default()
        font_cliente = ImageFont.load_default()
        font_data = ImageFont.load_default()

    texto_titulo = "RELATÓRIO DE RUPTURA"
    texto_cliente = f"CLIENTE: {nome_cliente}"
    periodo_str = f"Período: {str_data_inicio} a {str_data_fim}"
    gerado_em = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"

    def desenhar_centralizado(texto, fonte, y, cor):
        try:
            bbox = draw.textbbox((0, 0), texto, font=fonte)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = draw.textlength(texto, font=fonte)
        x = (width - text_width) / 2
        draw.text((x, y), texto, font=fonte, fill=cor)

    start_y_text = top_margin_logo + logo_height + 100 if logo_height > 0 else 300
    
    desenhar_centralizado(texto_titulo, font_titulo, start_y_text, azul_cx)
    desenhar_centralizado(texto_cliente, font_cliente, start_y_text + 180, preto)
    desenhar_centralizado(periodo_str, font_data, start_y_text + 350, cinza)
    desenhar_centralizado(gerado_em, font_data, start_y_text + 430, cinza)

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
    """
    Função de scroll blindada contra duplicatas.
    Usa um histórico de posições e uma tolerância mínima para evitar prints repetidos.
    """
    try:
        tabela_scroll = driver.find_element(By.XPATH, XPATH_SCROLL)
        # Reseta para o topo
        driver.execute_script("arguments[0].scrollTop = 0", tabela_scroll)
        time.sleep(1)

        # Medidas
        altura_total = driver.execute_script("return arguments[0].scrollHeight", tabela_scroll)
        altura_visivel = driver.execute_script("return arguments[0].clientHeight", tabela_scroll)
        
        # 1. Print Inicial (Topo)
        nome_arquivo = f"{nome_base}_pag{pagina_atual}_parte01.png"
        caminho_img = os.path.join(PASTA_FINAL, nome_arquivo)
        salvar_print_tratado(driver, caminho_img)
        lista_imagens.append(caminho_img)
        print(f"   -> Pag {pagina_atual} - Parte 1 capturada.")
        
        # CHECK DE SEGURANÇA: Se a tabela for pequena, PARA AQUI.
        # Adicionei +50 de tolerância para evitar o caso "APYCE" (onde sobra só um tiquinho de barra)
        if altura_total <= altura_visivel + 50:
            return 

        # 2. Loop de Scroll
        print(f"   -> Tabela longa. Iniciando scroll...")
        posicao_atual = 0
        parte = 2
        overlap = 100
        
        # Histórico para não repetir posições
        posicoes_printadas = {0} # Já printamos o 0

        while True:
            # Calcula próxima posição desejada
            nova_posicao_alvo = posicao_atual + altura_visivel - overlap
            max_scroll = altura_total - altura_visivel
            
            # Se passar do máximo, crava no máximo
            if nova_posicao_alvo > max_scroll:
                nova_posicao_alvo = max_scroll

            # ROLA PARA O ALVO
            driver.execute_script(f"arguments[0].scrollTop = {nova_posicao_alvo}", tabela_scroll)
            time.sleep(2)
            
            # LÊ A POSIÇÃO REAL (Onde o navegador realmente parou)
            posicao_real = driver.execute_script("return arguments[0].scrollTop", tabela_scroll)
            
            # CRITÉRIOS DE PARADA (ANTI-DUPLICAÇÃO)
            
            # 1. Se já printamos essa posição exata (loop infinito no final)
            if posicao_real in posicoes_printadas:
                break
            
            # 2. Se a diferença pro anterior for muito pequena (< 100px)
            # Isso evita tirar print de novo só pq andou 50 pixels (caso APYCE)
            if (posicao_real - posicao_atual) < 100:
                print(f"      [Info] Scroll final muito curto ({posicao_real - posicao_atual}px). Ignorando duplicata.")
                break

            # SE PASSOU NOS CRITÉRIOS: Tira o Print
            nome_arquivo = f"{nome_base}_pag{pagina_atual}_parte{parte:02d}.png"
            caminho_img = os.path.join(PASTA_FINAL, nome_arquivo)
            salvar_print_tratado(driver, caminho_img)
            lista_imagens.append(caminho_img)
            print(f"      Parte {parte} capturada (Pos: {posicao_real}).")
            
            # Atualiza controle
            posicoes_printadas.add(posicao_real)
            posicao_atual = posicao_real
            parte += 1
            
            # 3. Se já estamos no fundo, fim.
            if posicao_real >= max_scroll - 2: # -2px de tolerância
                break

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
    print(" ROBÔ DE RELATÓRIOS (FINAL SEM DUPLICATAS)")
    print(f" Pasta de Saída: {PASTA_FINAL}")
    print("="*50)
    input(">>> Quando carregado, APERTE ENTER <<<")

    configurar_filtro_data(driver)

    wait = WebDriverWait(driver, 20)
    wait_curto = WebDriverWait(driver, 4) 
    actions = ActionChains(driver)

    for nome_cliente, pasta_minio in CLIENTES.items():
        print(f"\n------------------------------------------------")
        print(f"Processando: {nome_cliente}")
        ajustar_zoom(driver, "100%")
        imagens_deste_cliente = []
        
        try:
            print("1. Filtrando Cliente...")
            botao_filtro = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_FILTRO)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_filtro)
            time.sleep(1)
            try: botao_filtro.click()
            except: driver.execute_script("arguments[0].click();", botao_filtro)
            time.sleep(1.5)

            try:
                caixa = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                caixa.click()
                time.sleep(0.5)
                caixa.send_keys(Keys.CONTROL + "a")
                caixa.send_keys(Keys.DELETE)
                time.sleep(0.5)
                print(f"   -> Digitando: {nome_cliente}")
                caixa.send_keys(nome_cliente)
                time.sleep(2.5)
            except:
                print("   -> Input não encontrado. Tentando digitação direta...")
                actions.send_keys(nome_cliente).perform()
                time.sleep(2.5)

            try:
                item_xpath = f"//div[@role='option' or contains(@class, 'item')]//*[contains(text(), '{nome_cliente}')]"
                item = wait_curto.until(EC.visibility_of_element_located((By.XPATH, item_xpath)))
                actions.move_to_element(item).perform()
                time.sleep(0.5)

                clicou_somente = False
                try:
                    btn_somente = driver.find_element(By.XPATH, "//span[contains(text(), 'Somente') or contains(text(), 'Only') or contains(text(), 'somente')]")
                    if btn_somente.is_displayed():
                        driver.execute_script("arguments[0].click();", btn_somente)
                        print("   -> Clicou em 'Somente'.")
                        clicou_somente = True
                except: pass

                if not clicou_somente:
                    print("   -> Botão 'Somente' não apareceu. Clicando no item...")
                    item.click()

            except TimeoutException:
                print(f"   ⚠️ CLIENTE '{nome_cliente}' NÃO ENCONTRADO na lista.")
                print("   -> Pulando...")
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                try: driver.find_element(By.TAG_NAME, "body").click()
                except: pass
                continue

            print("   -> Fechando menus para o print...")
            actions.send_keys(Keys.ESCAPE).perform()
            try: driver.execute_script("document.body.click();")
            except: pass
            try: driver.find_element(By.TAG_NAME, "header").click()
            except: 
                try: actions.move_by_offset(-5000, -5000).perform() 
                except: pass
            time.sleep(2)

            print("2. Aguardando dados (8s)...")
            time.sleep(8)

            nome_limpo = nome_cliente.replace("/", "-").replace("\\", "-")
            caminho_capa = criar_capa_personalizada(nome_limpo)
            if caminho_capa: imagens_deste_cliente.append(caminho_capa)

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