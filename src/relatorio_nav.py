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
        """ 
        Filtra usando BUSCA + SELECIONAR TUDO.
        Usa varredura global para encontrar itens visíveis.
        """
        print("\n📝 Configurando FILTRO DE JUSTIFICATIVAS...")
        wait = WebDriverWait(self.driver, 10)
        itens_selecionados = 0
        
        try:
            # 1. Abre menu
            abriu = False
            for xpath in cfg.XPATHS_BOTAO_JUSTIFICATIVA:
                if self.bot.clique_robusto(xpath, tentativas=2):
                    abriu = True
                    break
            if not abriu: 
                print("   ⚠️ Erro ao abrir menu de Justificativa.")
                return False
            time.sleep(2)

            # 2. Reset (Limpa Seleção)
            try:
                self.bot.clique_robusto(cfg.XPATH_CHECKBOX_HEADER)
                print("      ✅ Seleção Limpa (Reset).")
                time.sleep(1.5)
            except: pass

            # 3. Busca e Seleciona
            print(f"   -> Filtrando {len(cfg.LISTA_JUSTIFICATIVAS)} termos...")
            
            try:
                # Tenta achar input de busca (Qualquer input visível no painel)
                input_busca = WebDriverWait(self.driver, 4).until(EC.visibility_of_element_located((By.XPATH, cfg.XPATH_INPUT_BUSCA)))
                
                for termo in cfg.LISTA_JUSTIFICATIVAS:
                    print(f"      - Buscando: '{termo}'")
                    input_busca.click()
                    input_busca.send_keys(Keys.CONTROL + "a")
                    input_busca.send_keys(Keys.DELETE)
                    input_busca.send_keys(termo)
                    time.sleep(3) # Tempo aumentado para garantir renderização da lista
                    
                    # --- DETECÇÃO GLOBAL VISÍVEL ---
                    # Busca por md-checkboxes na página toda (//body//...)
                    # Como o menu é um overlay, eles estarão visíveis.
                    # Excluímos o header checkbox baseado em posição ou classe se necessário, mas geralmente ele é o primeiro.
                    
                    # Estratégia A: Buscar qualquer md-checkbox visível que NÃO seja o header
                    # O Header geralmente não está dentro de md-virtual-repeat-container
                    xpath_itens = "//md-virtual-repeat-container//md-checkbox"
                    
                    # Estratégia B: Fallback para divs com o texto
                    xpath_textos = f"//md-virtual-repeat-container//*[contains(text(), '{termo}')]"

                    # Coleta candidatos
                    candidatos = self.driver.find_elements(By.XPATH, f"{xpath_itens} | {xpath_textos}")
                    
                    # Filtra APENAS os visíveis
                    visiveis = [el for el in candidatos if el.is_displayed()]

                    if visiveis:
                        print(f"        -> [Encontrados] {len(visiveis)} itens visíveis.")
                        
                        # Tenta Header primeiro (Se houver muitos itens, é mais rápido)
                        if len(visiveis) > 1 and self.bot.clique_robusto(cfg.XPATH_CHECKBOX_HEADER, tentativas=1):
                             print(f"           -> [OK] Selecionados via Header.")
                             itens_selecionados += len(visiveis)
                        else:
                            # Fallback: Clica um por um
                            print(f"           -> [Fallback] Clicando um por um...")
                            for item in visiveis:
                                try:
                                    # Clica no centro do elemento via JS
                                    self.driver.execute_script("arguments[0].click();", item)
                                    time.sleep(0.2)
                                except: pass
                            itens_selecionados += len(visiveis)
                    else:
                        print(f"        -> [Vazio] Nenhuma ocorrência visual para '{termo}'.")
                
                # Limpa busca
                input_busca.send_keys(Keys.CONTROL + "a")
                input_busca.send_keys(Keys.DELETE)

            except Exception as e:
                print(f"   ⚠️ Erro na busca ({e}).")

            # Fecha menu
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
        """ Filtra cliente garantindo Seleção Única (Somente). """
        # Limpa estado
        try: self.driver.execute_script("document.body.click();")
        except: pass
        
        # Abre Filtro
        sucesso = False
        for xpath in cfg.XPATHS_FILTRO_CLIENTE:
            if self.bot.clique_robusto(xpath, tentativas=2):
                sucesso = True
                break
        if not sucesso:
            print("   ⚠️ Erro ao abrir filtro de Cliente.")
            return False

        time.sleep(1.5)
        
        # Digita
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
            # Localiza o item na lista
            item_xpath = f"//div[@role='option' or contains(@class, 'item')]//*[contains(text(), '{nome_cliente}')]"
            item = WebDriverWait(self.driver, 4).until(EC.visibility_of_element_located((By.XPATH, item_xpath)))
            
            # --- GARANTIA DE SELEÇÃO ÚNICA ---
            # Move o mouse para cima do item para revelar o botão "SOMENTE"
            ActionChains(self.driver).move_to_element(item).perform()
            time.sleep(0.5)
            
            clicou_somente = False
            try:
                # Busca o botão Somente que esteja visível
                btn_somente = WebDriverWait(self.driver, 2).until(
                    EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Somente') or contains(text(), 'Only') or contains(text(), 'somente')]"))
                )
                
                # Clica no Somente
                self.driver.execute_script("arguments[0].click();", btn_somente)
                print("   -> Clicou em 'Somente' (Seleção Única Garantida).")
                clicou_somente = True
            except:
                print("   ⚠️ Botão 'Somente' não apareceu.")

            # Se não conseguiu clicar em somente, clica no item (Fallback)
            # Nota: Isso pode misturar clientes se o filtro não limpou antes, mas é o melhor fallback possível
            if not clicou_somente:
                print("   -> Clicando no item (Fallback).")
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