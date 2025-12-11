import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import src.config as cfg

class RelatorioNav:
    def __init__(self, bot_driver):
        self.bot = bot_driver
        self.driver = bot_driver.driver

    def configurar_data(self):
        print(f"\n⏰ Configurando DATA: {cfg.label_periodo}...")
        wait = WebDriverWait(self.driver, 20)
        
        try:
            try:
                self.bot.clique_robusto(cfg.XPATH_CALENDARIO)
            except:
                self.driver.find_element(By.CSS_SELECTOR, ".ga-date-range-picker").click()
            time.sleep(1.5)

            self.bot.clique_robusto(cfg.XPATH_DROPDOWN)
            time.sleep(1.5)

            # LÓGICA DINÂMICA: SEGUNDA vs OUTROS DIAS
            if not cfg.eh_segunda:
                print("   -> Selecionando opção 'Ontem'...")
                self.bot.clique_robusto(cfg.XPATH_OPCAO_ONTEM)
                time.sleep(1.5)
            else:
                print("   -> Selecionando 'Avançado' (Segunda-feira)...")
                try:
                    avanc = wait.until(EC.element_to_be_clickable((By.XPATH, cfg.XPATH_OPCAO_AVANCADO)))
                    avanc.click()
                except Exception as e:
                    print(f"      ⚠️ Falha ao clicar em Avançado: {e}")
                    return

                time.sleep(1.5)
                print(f"   -> Configurando 'Menos {cfg.DIAS_PARA_SUBTRAIR} dias'...")
                
                self._preencher_input(cfg.XPATH_INPUT_DIAS_INICIO, str(cfg.DIAS_PARA_SUBTRAIR), wait)
                self._preencher_input(cfg.XPATH_INPUT_DIAS_FIM, str(cfg.DIAS_PARA_SUBTRAIR), wait)

            try:
                try: self.driver.find_element(By.XPATH, "//div[contains(@class, 'cdk-overlay-pane')]").click()
                except: pass
                
                btn_aplicar = wait.until(EC.element_to_be_clickable((By.XPATH, cfg.XPATH_BTN_APLICAR)))
                self.driver.execute_script("arguments[0].click();", btn_aplicar)
            except TimeoutException:
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            
            time.sleep(6)
            print("✅ Filtro de data aplicado.")
        except Exception as e:
            print(f"❌ Erro Data: {e}")

    def _preencher_input(self, xpath, valor, wait):
        try:
            inp = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
            inp.clear()
            time.sleep(0.3)
            inp.send_keys(Keys.BACKSPACE * 5)
            inp.send_keys(valor)
        except Exception as e:
            print(f"      ❌ Erro input ({xpath}): {e}")

    def configurar_justificativas(self):
        """ Filtra usando BUSCA + SELECIONAR TUDO (Híbrido) """
        print("\n📝 Configurando FILTRO DE JUSTIFICATIVAS...")
        wait = WebDriverWait(self.driver, 10)
        itens_selecionados = 0
        
        try:
            abriu = False
            for xpath in cfg.XPATHS_BOTAO_JUSTIFICATIVA:
                if self.bot.clique_robusto(xpath, tentativas=2):
                    abriu = True
                    break
            if not abriu: 
                print("   ⚠️ Erro ao abrir menu de Justificativa.")
                return False
            time.sleep(2)

            # Reset
            try:
                self.bot.clique_robusto(cfg.XPATH_CHECKBOX_HEADER)
                print("      ✅ Seleção Limpa.")
                time.sleep(1.5)
            except: pass

            print(f"   -> Filtrando {len(cfg.LISTA_JUSTIFICATIVAS)} termos...")
            
            try:
                input_busca = WebDriverWait(self.driver, 4).until(EC.visibility_of_element_located((By.XPATH, cfg.XPATH_INPUT_BUSCA)))
                
                for termo in cfg.LISTA_JUSTIFICATIVAS:
                    print(f"      - Buscando: '{termo}'")
                    input_busca.click()
                    input_busca.send_keys(Keys.CONTROL + "a")
                    input_busca.send_keys(Keys.DELETE)
                    input_busca.send_keys(termo)
                    time.sleep(2) 
                    
                    # Detecção Híbrida: Busca textos ou checkboxes visíveis
                    xpath_res = f"//div[contains(@class, 'cdk-overlay-pane')]//*[contains(text(), '{termo}')] | //div[contains(@class, 'cdk-overlay-pane')]//md-checkbox"
                    visiveis = [el for el in self.driver.find_elements(By.XPATH, xpath_res) if el.is_displayed()]

                    if visiveis:
                        # Tenta Header primeiro (mais rápido)
                        if self.bot.clique_robusto(cfg.XPATH_CHECKBOX_HEADER, tentativas=1):
                            print(f"        -> [OK] Selecionados {len(visiveis)} itens (Header).")
                            itens_selecionados += 1
                        else:
                            # Fallback: Clica no primeiro item
                            self.driver.execute_script("arguments[0].click();", visiveis[0])
                            itens_selecionados += 1
                    else:
                        print(f"        -> [Vazio] Nenhuma ocorrência para '{termo}'.")
                
                input_busca.send_keys(Keys.CONTROL + "a")
                input_busca.send_keys(Keys.DELETE)

            except Exception as e:
                print(f"   ⚠️ Erro na busca ({e}).")

            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            try: self.driver.find_element(By.TAG_NAME, "body").click()
            except: pass
            
            if itens_selecionados > 0:
                print(f"✅ Filtros aplicados.")
                time.sleep(5)
                return True
            else:
                print("⚠️ Nenhuma justificativa encontrada.")
                return False

        except Exception as e:
            print(f"❌ Erro Crítico Justificativas: {e}")
            return False

    def filtrar_cliente(self, nome_cliente):
        try: self.driver.execute_script("document.body.click();")
        except: pass
        
        sucesso = False
        for xpath in cfg.XPATHS_FILTRO_CLIENTE:
            if self.bot.clique_robusto(xpath, tentativas=2):
                sucesso = True
                break
        if not sucesso:
            print("   ⚠️ Erro ao abrir filtro de Cliente.")
            return False

        time.sleep(1.5)
        
        try:
            caixa = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            caixa.click()
            time.sleep(0.5)
            caixa.send_keys(Keys.CONTROL + "a")
            caixa.send_keys(Keys.DELETE)
            time.sleep(0.5)
            print(f"   -> Digitando: {nome_cliente}")
            caixa.send_keys(nome_cliente)
            time.sleep(2.5)
        except:
            print("   -> Input não encontrado.")
            return False

        try:
            item_xpath = f"//div[@role='option' or contains(@class, 'item')]//*[contains(text(), '{nome_cliente}')]"
            item = WebDriverWait(self.driver, 4).until(EC.visibility_of_element_located((By.XPATH, item_xpath)))
            
            clicou_somente = False
            try:
                btn_somente = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Somente') or contains(text(), 'Only') or contains(text(), 'somente')]")
                if btn_somente.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn_somente)
                    print("   -> Clicou em 'Somente'.")
                    clicou_somente = True
            except: pass

            if not clicou_somente:
                item.click()
            
            return True

        except TimeoutException:
            try: caixa.send_keys(Keys.ENTER)
            except: pass
            raise TimeoutException("Cliente não encontrado na lista")

    def fechar_menus(self):
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        try: self.driver.execute_script("document.body.click();")
        except: pass
        try: self.driver.find_element(By.TAG_NAME, "header").click()
        except: 
            try: ActionChains(self.driver).move_by_offset(-5000, -5000).perform() 
            except: pass