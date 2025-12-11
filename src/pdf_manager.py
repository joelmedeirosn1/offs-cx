import os
import glob
import time
from PIL import Image, ImageDraw, ImageFont
from selenium.webdriver.common.by import By
from datetime import datetime
import src.config as cfg

class PDFManager:
    def __init__(self, bot_driver):
        self.bot = bot_driver
        self.driver = bot_driver.driver

    def limpar_pasta_temporaria(self):
        print(f"--- Limpando pasta: {cfg.PASTA_FINAL} ---")
        files = glob.glob(os.path.join(cfg.PASTA_FINAL, "*"))
        for f in files:
            try: os.remove(f)
            except: pass
        print("Pasta limpa.\n")

    def criar_capa(self, nome_cliente):
        print(f"   -> Gerando Capa...")
        width = cfg.PADRAO_LARGURA 
        height = cfg.PADRAO_ALTURA 
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        azul_cx = (0, 51, 102)
        preto = (0, 0, 0)
        cinza = (100, 100, 100)
        
        caminho_logo = None
        possiveis_logos = ["cxtrade_logo.jpg", "logo_cx.png", "logo_cx.jpg"]
        for nome in possiveis_logos:
            temp = os.path.join(cfg.PASTA_DIR, nome)
            if os.path.exists(temp):
                caminho_logo = temp
                break
        
        top_margin_logo = 80
        logo_height = 0
        if caminho_logo:
            try:
                logo = Image.open(caminho_logo)
                base_width = 400
                w_percent = (base_width / float(logo.size[0]))
                h_size = int((float(logo.size[1]) * float(w_percent)))
                logo = logo.resize((base_width, h_size), Image.Resampling.LANCZOS)
                x = int((width - base_width) / 2)
                if logo.mode == 'RGBA': img.paste(logo, (x, top_margin_logo), logo)
                else: img.paste(logo, (x, top_margin_logo))
                logo_height = h_size
            except: pass

        try:
            f_tit = ImageFont.truetype("arial.ttf", 110)
            f_cli = ImageFont.truetype("arial.ttf", 80)
            f_dat = ImageFont.truetype("arial.ttf", 50)
        except:
            f_tit = ImageFont.load_default()
            f_cli = f_tit
            f_dat = f_tit

        texto_titulo = "RELATÓRIO - OFF'S"
        texto_gerado = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"

        def draw_center(txt, fnt, y, cor):
            try:
                bb = draw.textbbox((0,0), txt, font=fnt)
                w = bb[2]-bb[0]
            except: w = draw.textlength(txt, font=fnt)
            draw.text(((width-w)/2, y), txt, font=fnt, fill=cor)

        start_y = top_margin_logo + logo_height + 100 if logo_height > 0 else 300
        draw_center(texto_titulo, f_tit, start_y, azul_cx)
        draw_center(f"CLIENTE: {nome_cliente}", f_cli, start_y + 180, preto)
        draw_center(f"Período: {cfg.texto_periodo_filtro}", f_dat, start_y + 350, cinza)
        draw_center(texto_gerado, f_dat, start_y + 430, cinza)

        nome_arq = f"{nome_cliente}_00_CAPA.png".replace("/", "-")
        path = os.path.join(cfg.PASTA_FINAL, nome_arq)
        img.save(path)
        return path

    def capturar_scroll(self, nome_base, pagina_atual, lista_imagens):
        try:
            tabela = self.driver.find_element(By.XPATH, cfg.XPATH_SCROLL)
            self.driver.execute_script("arguments[0].scrollTop = 0", tabela)
            time.sleep(1)
            
            h_total = self.driver.execute_script("return arguments[0].scrollHeight", tabela)
            h_visivel = self.driver.execute_script("return arguments[0].clientHeight", tabela)
            
            arq = f"{nome_base}_pag{pagina_atual}_parte01.png"
            path = os.path.join(cfg.PASTA_FINAL, arq)
            self._salvar_print_tratado(path)
            lista_imagens.append(path)
            print(f"   -> Pag {pagina_atual} - Parte 1 capturada.")

            if h_total <= h_visivel + 50: return

            print(f"   -> Tabela longa. Iniciando scroll...")
            pos = 0
            parte = 2
            overlap = 100
            printadas = {0}
            
            while True:
                alvo = pos + h_visivel - overlap
                if alvo > h_total - h_visivel: alvo = h_total - h_visivel
                
                self.driver.execute_script(f"arguments[0].scrollTop = {alvo}", tabela)
                time.sleep(2)
                
                real = self.driver.execute_script("return arguments[0].scrollTop", tabela)
                if real in printadas: break
                if (real - pos) < 100: break
                
                arq = f"{nome_base}_pag{pagina_atual}_parte{parte:02d}.png"
                path = os.path.join(cfg.PASTA_FINAL, arq)
                self._salvar_print_tratado(path)
                lista_imagens.append(path)
                
                print(f"      Parte {parte} capturada (Pos: {real}).")
                printadas.add(real)
                pos = real
                parte += 1
                
                if real >= (h_total - h_visivel) - 2: break
        except Exception as e:
            print(f"   [Erro Scroll]: {e}")
            try:
                arq = f"{nome_base}_pag{pagina_atual}_ERRO.png"
                path = os.path.join(cfg.PASTA_FINAL, arq)
                self.driver.save_screenshot(path)
                lista_imagens.append(path)
            except: pass

    def tentar_paginar(self):
        """ Tenta clicar na seta de próxima página se estiver ativa """
        try:
            botao_proximo = self.driver.find_element(By.XPATH, cfg.XPATH_PAGINACAO)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_proximo)
            
            classes = botao_proximo.get_attribute("class")
            aria_disabled = botao_proximo.get_attribute("aria-disabled")
            
            if "disabled" in str(classes) or aria_disabled == "true":
                return False 
            
            self.driver.execute_script("arguments[0].click();", botao_proximo)
            return True 
        except:
            return False

    def _salvar_print_tratado(self, caminho):
        self.driver.save_screenshot(caminho)
        img = Image.open(caminho)
        w, h = img.size
        img = img.crop((0, cfg.ALTURA_CORTE_BARRA_SUPERIOR, w, h))
        w2, h2 = img.size
        novo_h = h2 + cfg.MARGEM_SUPERIOR_EXTRA
        nova = Image.new("RGB", (w2, novo_h), img.getpixel((0,0)))
        nova.paste(img, (0, cfg.MARGEM_SUPERIOR_EXTRA))
        nova.save(caminho)
        img.close()

    def gerar_pdf(self, nome_cliente, lista_imagens):
        if not lista_imagens: return
        print(f"   -> Gerando PDF ({len(lista_imagens)} pág)...")
        try:
            ini = Image.open(lista_imagens[0])
            if ini.mode == 'RGBA': ini = ini.convert('RGB')
            restantes = []
            for p in lista_imagens[1:]:
                im = Image.open(p)
                if im.mode == 'RGBA': im = im.convert('RGB')
                restantes.append(im)
            
            nome_pdf = f"{nome_cliente}.pdf".replace("/", "-")
            path = os.path.join(cfg.PASTA_FINAL, nome_pdf)
            ini.save(path, save_all=True, append_images=restantes)
            print(f"   [SUCESSO] PDF Criado: {path}")
            
            ini.close()
            for im in restantes: im.close()
            for p in lista_imagens:
                try: os.remove(p)
                except: pass
        except Exception as e:
            print(f"   [ERRO PDF]: {e}")