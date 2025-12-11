import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import src.config as cfg

class BotDriver:
    def __init__(self):
        self.driver = self.iniciar_navegador()

    def iniciar_navegador(self):
        print("--- Iniciando Robô ---")
        options = Options()
        options.add_argument(f"user-data-dir={cfg.PASTA_PERFIL_BOT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(cfg.PADRAO_LARGURA, cfg.PADRAO_ALTURA)
        return driver

    def get(self, url):
        self.driver.get(url)

    def quit(self):
        self.driver.quit()

    def ajustar_zoom(self, nivel):
        try: self.driver.execute_script(f"document.body.style.zoom='{nivel}'")
        except: pass

    def clique_robusto(self, xpath, tentativas=3):
        """
        Tenta clicar em um elemento de forma resiliente a StaleElementReferenceException.
        """
        for i in range(tentativas):
            try:
                # Timeout curto para permitir retentativas rápidas
                elemento = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                time.sleep(0.2)
                elemento.click()
                return True
            except StaleElementReferenceException:
                time.sleep(0.5)
                continue
            except Exception as e:
                if i == tentativas - 1:
                    # Fallback JS na última tentativa
                    try:
                        ele = self.driver.find_element(By.XPATH, xpath)
                        self.driver.execute_script("arguments[0].click();", ele)
                        return True
                    except:
                        pass
                time.sleep(0.5)
        return False