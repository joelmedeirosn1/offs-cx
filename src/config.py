import os
import sys
from datetime import datetime, timedelta

# ================= CONFIGURAÇÃO GERAL =================
PADRAO_LARGURA = 1920
PADRAO_ALTURA = 1080
WAIT_TIMEOUT = 10

# ================= PASTAS =================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DIR = ROOT_DIR 
PASTA_PERFIL_BOT = os.path.join(ROOT_DIR, "perfil_bot")
PASTA_RAIZ_FOTOS = r"C:\Users\RT-121\Documents\RT\cx off-20251125T174423Z-1-001\cx off\fotos"

# ================= CÁLCULO DE DATAS (AUTOMÁTICO) =================
hoje = datetime.now()
# Para testar segunda-feira manualmente, descomente a linha abaixo:
# hoje = datetime(2025, 12, 8) 

if hoje.weekday() == 0:
    # SEGUNDA-FEIRA: Busca Sábado (-2 dias) via menu Avançado
    DIAS_PARA_SUBTRAIR = 2
    data_alvo = hoje - timedelta(days=DIAS_PARA_SUBTRAIR)
    label_periodo = "Sábado Passado (-2 dias)"
    eh_segunda = True
else:
    # OUTROS DIAS: Busca Ontem (-1 dia) via menu Ontem
    DIAS_PARA_SUBTRAIR = 1
    data_alvo = hoje - timedelta(days=1)
    label_periodo = "Dia Anterior (Ontem)"
    eh_segunda = False

str_data_inicio = data_alvo.strftime('%d/%m/%Y')
str_data_fim = data_alvo.strftime('%d/%m/%Y')
texto_periodo_filtro = f"{str_data_inicio}" 

# Nome da pasta do dia (Ex: Relatorios_06-12)
nome_pasta_data = f"Relatorios_{data_alvo.strftime('%d-%m')}"
PASTA_FINAL = os.path.join(PASTA_RAIZ_FOTOS, nome_pasta_data)

if not os.path.exists(PASTA_FINAL):
    os.makedirs(PASTA_FINAL)

# ================= XPATHS =================
# Cliente
XPATHS_FILTRO_CLIENTE = [
    "(//canvas-control-wrapper//*[contains(text(), 'CLIENTE')])[1]",
    "(//*[contains(text(), 'CLIENTE')])[2]",
    'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[5]/ng2-canvas-component[1]/div[1]/div[1]/div[1]'
]

# Tabela
XPATH_SCROLL = "id('body')/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[3]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]"
XPATH_PAGINACAO = 'id("body")/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[3]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]/table-wrapper[1]/div[1]/ng2-table[1]/div[1]/div[6]/div[3]'

# Data
XPATH_CALENDARIO = "//mat-icon[contains(text(),'calendar')]/ancestor::div[1]"
XPATH_DROPDOWN = "//span[contains(text(), 'Fixo') or contains(text(), 'Automático') or contains(text(), 'Período') or contains(text(), 'Últimos') or contains(text(), 'Semana')]"
XPATH_OPCAO_FIXO = "//span[contains(text(), 'Fixo')]" 
XPATH_OPCAO_ONTEM = "//span[contains(text(), 'Ontem')]"
XPATH_OPCAO_AVANCADO = "//div[contains(@class, 'cdk-overlay-pane')]//span[contains(text(), 'Avançado')]"
XPATH_INPUT_DIAS_INICIO = 'id("mat-input-0")' 
XPATH_INPUT_DIAS_FIM = 'id("mat-input-1")' 
XPATH_BTN_APLICAR = "//button[.//span[contains(text(), 'Aplicar')] or contains(text(), 'Aplicar')]"

# Justificativa
XPATHS_BOTAO_JUSTIFICATIVA = [
    "(//canvas-control-wrapper//*[contains(text(), 'JUSTIFICATIVA')])[1]",
    '//body/div[2]/div[1]/ng2-reporting-plate[1]/plate[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/canvas-pancake-adapter[1]/canvas-layout[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ng2-report[1]/ng2-canvas-container[1]/div[1]/div[6]/ng2-canvas-component[1]/div[1]/div[1]/div[1]/div[1]/canvas-control-wrapper[1]/upgraded-canvas-control[1]/canvas-control-host[1]/control-layout-wrapper[1]/button[1]/div[1]/span[2]/span[1]/main-section[1]',
    "(//*[contains(text(), 'JUSTIFICATIVA')])[2]"
]
XPATH_CHECKBOX_HEADER = "//body/canvas-control-editor[1]/div[1]/div[1]/div[1]/list-control[1]/div[1]/div[1]/md-checkbox[1]/div[2]"
XPATH_INPUT_BUSCA = "id('input-2') | //input[contains(@placeholder, 'pesquisar')]"

# ================= LISTAS =================
sys.path.append(ROOT_DIR) 
try:
    from src.config_justificativas import LISTA_JUSTIFICATIVAS
except ImportError:
    LISTA_JUSTIFICATIVAS = ["ATESTADO", "DECLARAÇÃO","LICENÇA MATERNIDADE" , "LICENÇA PATERNIDADE"]

# Garante Maiúsculas
LISTA_JUSTIFICATIVAS = [x.upper() for x in LISTA_JUSTIFICATIVAS]

# Variáveis de Layout
ALTURA_CORTE_BARRA_SUPERIOR = 80
MARGEM_SUPERIOR_EXTRA = 100