import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Importa nossas configurações e funções
from config_clientes import CLIENTES, URL_RELATORIO
from salvar_minio import enviar_arquivo

# --- Configuração de Pastas ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DRIVER_PATH = os.path.join(PROJECT_ROOT, "drivers", "chromedriver.exe")
FOTOS_DIR = os.path.join(PROJECT_ROOT, "fotos")
os.makedirs(FOTOS_DIR, exist_ok=True)

def iniciar_browser():
    """Inicia o Chrome usando o perfil de usuário para manter o login."""
    options = webdriver.ChromeOptions()
    
    # --- CONFIGURAÇÃO CRÍTICA PARA LOGIN GOOGLE ---
    # Isso faz o robô usar o SEU Chrome real, já logado no Looker Studio.
    # Você precisa fechar todas as janelas do Chrome antes de rodar isso.
    # Ajuste o caminho abaixo para o seu usuário do Windows:
    user_data = r"C:\Users\RT-121\AppData\Local\Google\Chrome\User Data"
    options.add_argument(f"--user-data-dir={user_data}")
    # options.add_argument("--profile-directory=Default") # Use se tiver mais de um perfil
    
    options.add_argument("--start-maximized")
    
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def processar_relatorios():
    driver = iniciar_browser()
    
    try:
        print(f"Acessando relatório: {URL_RELATORIO}")
        driver.get(URL_RELATORIO)
        
        # Espera inicial para carregar o Looker Studio (pode ser lento)
        time.sleep(10) 

        # --- SELETORES (VOCÊ PRECISA AJUSTAR ESSES XPATHS) ---
        # Dica: No Chrome, botão direito no elemento -> Inspecionar -> Botão direito no HTML -> Copy -> Copy XPath
        
        # 1. XPath do Botão Dropdown "CLIENTE" (A setinha ou a caixa onde clica para abrir a lista)
        XPATH_DROPDOWN_CLIENTE = '//div[@class="class-do-dropdown"]' # <--- SUBSTITUA AQUI

        # 2. XPath do Campo de Busca dentro do Dropdown (para digitar o nome do cliente)
        XPATH_CAMPO_BUSCA = '//input[@type="text"]' # <--- SUBSTITUA AQUI
        
        # 3. XPath do Checkbox "Selecionar Tudo" (Geralmente clicamos nele para limpar a seleção anterior)
        XPATH_CHECKBOX_SOMENTE = '//div[text()="Somente"]' # <--- Exemplo, varia muito

        # 4. XPath da TABELA (Elemento principal que queremos tirar print)
        XPATH_TABELA = '//div[@class="class-da-tabela"]' # <--- SUBSTITUA AQUI
        
        # 5. Clica fora ou botão aplicar (se houver) para fechar o dropdown
        XPATH_TITULO_RELATORIO = '//div[text()="OFF\'S - CX"]' # Um lugar seguro para clicar e fechar o menu

        for nome_cliente, pasta_minio in CLIENTES.items():
            print(f"\n--- Processando: {nome_cliente} ---")
            
            # 1. Clicar no Dropdown
            botao_filtro = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, XPATH_DROPDOWN_CLIENTE)))
            botao_filtro.click()
            time.sleep(1)

            # 2. Digitar o nome do cliente no filtro
            campo_busca = driver.find_element(By.XPATH, XPATH_CAMPO_BUSCA)
            campo_busca.send_keys(Keys.CONTROL + "a") # Seleciona texto antigo
            campo_busca.send_keys(Keys.DELETE)        # Apaga
            campo_busca.send_keys(nome_cliente)       # Digita o novo
            time.sleep(2)

            # 3. Selecionar a opção "Somente" (No Looker, ao passar o mouse ou buscar, geralmente aparece "Somente" para selecionar só aquele)
            # Essa parte é a mais chata do Looker. Pode precisar de ajuste manual.
            # Vamos tentar clicar no primeiro checkbox que aparecer após a busca
            primeiro_checkbox = driver.find_element(By.XPATH, f"//div[@aria-label='{nome_cliente}']//div[@class='checkbox-class']") 
            primeiro_checkbox.click()
            
            # 4. Fechar o filtro (Clica no título para sair do menu)
            driver.find_element(By.XPATH, XPATH_TITULO_RELATORIO).click()
            
            # 5. Esperar a tabela atualizar (importante!)
            print("Aguardando atualização da tabela...")
            time.sleep(5) 

            # 6. Tirar Print da Tabela
            elemento_tabela = driver.find_element(By.XPATH, XPATH_TABELA)
            nome_arquivo = f"OFF_s_{nome_cliente}.png"
            caminho_foto = os.path.join(FOTOS_DIR, nome_arquivo)
            
            elemento_tabela.screenshot(caminho_foto)
            print(f"📸 Print salvo: {caminho_foto}")

            # 7. Enviar para MinIO na pasta correta
            enviar_arquivo(caminho_foto, pasta_destino=pasta_minio)

    except Exception as e:
        print(f"❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("Finalizando navegador...")
        # driver.quit() # Comentei para você ver o resultado sem fechar na cara

if __name__ == "__main__":
    processar_relatorios()