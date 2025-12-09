import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# ================= CONFIGURAÇÃO =================
PASTA_PERFIL_BOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perfil_bot")
# URL DO SEU RELATÓRIO
URL_RELATORIO = "https://lookerstudio.google.com/u/0/reporting/ada033a0-55d4-4d59-981e-d65bd7e1a581/page/8gyPF" 

def highlight(driver, element):
    """ Coloca uma borda vermelha e fundo amarelo no elemento """
    try:
        driver.execute_script("arguments[0].style.border='4px solid red'; arguments[0].style.backgroundColor='yellow';", element)
    except: pass

def remove_highlight(driver, element):
    try:
        driver.execute_script("arguments[0].style.border='none'; arguments[0].style.backgroundColor='';", element)
    except: pass

def gerar_xpath_do_elemento(driver, element):
    """ Tenta descobrir um XPath único para o elemento que o usuário clicou """
    return driver.execute_script("""
        gPt=function(c){
            if(c.id!==''){return'id("'+c.id+'")'}
            if(c===document.body){return c.tagName}
            var a=0;
            var e=c.parentNode.childNodes;
            for(var b=0;b<e.length;b++){
                var d=e[b];
                if(d===c){return gPt(c.parentNode)+'/'+c.tagName+'['+(a+1)+']'}
                if(d.nodeType===1&&d.tagName===c.tagName){a++}
            }
        };
        return gPt(arguments[0]);
    """, element)

def capturar_clique_manual(driver, nome_etapa):
    """ Se o automático falhar, pede ajuda ao usuário """
    print(f"\n⚠️  [MODO MANUAL] Não achei o '{nome_etapa}' automaticamente.")
    print(f"👉  Vá na janela do Chrome aberta, CLIQUE no '{nome_etapa}' e volte aqui.")
    input(">>> DEPOIS DE CLICAR NO ELEMENTO, APERTE ENTER AQUI <<<")
    
    try:
        # Pega o elemento que está focado (o último clicado)
        elemento_ativo = driver.switch_to.active_element
        xpath_gerado = gerar_xpath_do_elemento(driver, elemento_ativo)
        
        print(f"✅  Capturado! O XPath do elemento que você clicou é:")
        print(f"    {xpath_gerado}")
        
        highlight(driver, elemento_ativo)
        time.sleep(1)
        remove_highlight(driver, elemento_ativo)
        
        return elemento_ativo, xpath_gerado
    except Exception as e:
        print(f"❌  Erro ao capturar clique manual: {e}")
        return None, None

def testar_lista_xpaths(driver, lista_xpaths, nome_etapa):
    print(f"\n🔎  Procurando: {nome_etapa}")
    
    # 1. Tenta Automático
    for xpath in lista_xpaths:
        try:
            elementos = driver.find_elements(By.XPATH, xpath)
            for elem in elementos:
                if elem.is_displayed():
                    highlight(driver, elem)
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    print(f"   [ACHEI?] XPath: {xpath}")
                    confirma = input("   Este é o botão correto? (s = Sim / n = Não / m = Mudar p/ Manual): ").strip().lower()
                    remove_highlight(driver, elem)
                    
                    if confirma == 's':
                        print(f"   ✅ Confirmado.")
                        return elem, xpath
                    elif confirma == 'm':
                        break # Sai do loop e vai para o manual
        except:
            pass
    
    # 2. Se falhar, vai para Manual
    return capturar_clique_manual(driver, nome_etapa)

def iniciar_navegador():
    print("--- Iniciando Robô de Rastreamento ---")
    options = Options()
    options.add_argument(f"user-data-dir={PASTA_PERFIL_BOT}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

# ================= LISTAS DE XPATHS (Ampliada) =================

XPATHS_1_CALENDARIO = [
    # Tenta pegar pelo ícone de calendário
    "//mat-icon[contains(text(),'calendar')]/ancestor::div[@role='button']",
    "//mat-icon[contains(text(),'calendar')]/ancestor::div[1]",
    # Tenta pegar por qualquer caixa que pareça um date picker
    "//div[contains(@class, 'ga-date-range-picker')]",
    "//div[contains(@class, 'date-range')]",
    # Tenta pegar texto de data (Ex: 25 de nov) - AJUSTE SE NECESSÁRIO
    "//*[contains(text(), '2024') or contains(text(), '2025')]/ancestor::div[@role='button']"
]

XPATHS_2_DROPDOWN_TIPO = [
    "//div[contains(@class, 'mat-select-trigger')]",
    "//span[contains(text(), 'Fixo') or contains(text(), 'Automático') or contains(text(), 'Período')]",
]

XPATHS_3_CATEGORIA_7DIAS = [
    "//mat-option//span[contains(text(), 'Últimos 7 dias')]",
    "//mat-option//span[contains(text(), 'Last 7 days')]",
    "//span[contains(text(), 'Últimos 7 dias')]" # Genérico
]

XPATHS_4_OPCAO_FINAL = [
    # Pega o último span com esse texto na tela (geralmente o do submenu)
    "(//span[contains(text(), 'Últimos 7 dias')])[last()]",
    "//div[contains(@class, 'mat-menu-panel')]//span[contains(text(), 'Últimos 7 dias')]"
]

XPATHS_5_APLICAR = [
    "//button[contains(text(), 'Aplicar')]",
    "//button[contains(text(), 'Apply')]",
]

def executar_rastreamento():
    driver = iniciar_navegador()
    driver.get(URL_RELATORIO)
    
    print("\n" + "="*60)
    print(" INSTRUÇÕES:")
    print(" 1. Espere o relatório carregar e você ver a data.")
    print(" 2. Se o robô não achar o botão, ele vai te pedir para CLICAR nele.")
    print("="*60 + "\n")
    
    input(">>> Quando estiver pronto, APERTE ENTER <<<")

    # Inicializa variáveis para evitar erro de UnboundLocalError
    xpath1 = xpath2 = xpath3 = xpath4 = xpath5 = "Não encontrado"

    # Passo 1
    elem1, xpath1 = testar_lista_xpaths(driver, XPATHS_1_CALENDARIO, "Botão Calendário")
    if elem1: 
        elem1.click()
        time.sleep(2) 

        # Passo 2
        elem2, xpath2 = testar_lista_xpaths(driver, XPATHS_2_DROPDOWN_TIPO, "Dropdown Tipo Período")
        if elem2:
            elem2.click()
            time.sleep(2) 

            # Passo 3
            elem3, xpath3 = testar_lista_xpaths(driver, XPATHS_3_CATEGORIA_7DIAS, "Opção 'Últimos 7 dias'")
            if elem3:
                elem3.click()
                time.sleep(2)

                # Passo 4 (Submenu)
                print("--- Verificando Submenu ---")
                elem4, xpath4 = testar_lista_xpaths(driver, XPATHS_4_OPCAO_FINAL, "Opção Final do Submenu")
                if elem4:
                    elem4.click()
                    time.sleep(1)
            
            ActionChains(driver).send_keys(u'\ue00c').perform() # ESC
            time.sleep(1)

        # Passo 5
        elem5, xpath5 = testar_lista_xpaths(driver, XPATHS_5_APLICAR, "Botão Aplicar")

    print("\n\n=== 📋 RESUMO FINAL (Copie os XPaths encontrados) ===")
    print(f"1. Calendário:   {xpath1}")
    print(f"2. Dropdown:     {xpath2}")
    print(f"3. Categoria:    {xpath3}")
    print(f"4. Submenu:      {xpath4}")
    print(f"5. Aplicar:      {xpath5}")
    
    input("\n✅ Teste finalizado. Enter para fechar...")
    driver.quit()

if __name__ == "__main__":
    executar_rastreamento()