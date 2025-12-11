import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ================= CONFIGURAÇÕES DO TEMPLATE =================
# Coordenadas do Campo CLIENTE (O segundo campo da pilha à direita)
AREA_CLIENTE = (1450, 145, 1780, 185) 

# Coordenadas do Campo DATA (O terceiro campo da pilha à direita)
AREA_DATA = (1450, 195, 1780, 235)

def criar_relatorio_vazio(nome_cliente, texto_periodo, pasta_saida, pasta_raiz):
    """
    Gera um PDF composto por:
    1. Capa (Gerada programaticamente)
    2. Página 2 (Template de imagem editado com nome e data)
    """
    
    print(f"   -> Iniciando geração de PDF 'Sem Dados' para: {nome_cliente}")
    
    # 1. Caminho do Template (A imagem base que você salvou)
    caminho_template = os.path.join(pasta_raiz, "template_sem_dados.png")
    
    if not os.path.exists(caminho_template):
        print(f"   ❌ ERRO: Arquivo 'template_sem_dados.png' não encontrado em {pasta_raiz}")
        print("      Salve um print da tela vazia com esse nome na pasta do projeto.")
        return

    try:
        # --- GERAR CAPA ---
        caminho_capa = gerar_capa(nome_cliente, texto_periodo, pasta_saida, pasta_raiz)
        
        # --- EDITAR PÁGINA 2 (TEMPLATE) ---
        img_template = Image.open(caminho_template).convert("RGB")
        draw = ImageDraw.Draw(img_template)
        
        # Fontes
        try:
            font_filtro = ImageFont.truetype("arial.ttf", 18)
            font_bold = ImageFont.truetype("arialbd.ttf", 18) 
        except:
            font_filtro = ImageFont.load_default()
            font_bold = font_filtro

        # Cores
        cor_branca = (255, 255, 255)
        cor_preta = (0, 0, 0)

        # -- EDIÇÃO 1: NOME DO CLIENTE --
        draw.rectangle(AREA_CLIENTE, fill=cor_branca)
        draw.text((AREA_CLIENTE[0] + 5, AREA_CLIENTE[1] + 8), nome_cliente, font=font_bold, fill=cor_preta)

        # -- EDIÇÃO 2: PERÍODO (DATA) --
        draw.rectangle(AREA_DATA, fill=cor_branca)
        draw.text((AREA_DATA[0] + 5, AREA_DATA[1] + 8), texto_periodo, font=font_filtro, fill=cor_preta)

        # Salva a imagem editada temporariamente
        caminho_pag2 = os.path.join(pasta_saida, f"temp_{nome_cliente}_vazio.png")
        img_template.save(caminho_pag2)
        
        # --- JUNTAR EM PDF (COM NOME 'no data') ---
        img_capa = Image.open(caminho_capa).convert("RGB")
        img_p2 = Image.open(caminho_pag2).convert("RGB")
        
        # ADICIONANDO "no data" AO NOME DO ARQUIVO
        nome_pdf = f"{nome_cliente} no data.pdf".replace("/", "-")
        caminho_pdf = os.path.join(pasta_saida, nome_pdf)
        
        img_capa.save(caminho_pdf, save_all=True, append_images=[img_p2])
        
        print(f"   ✅ PDF Vazio gerado com sucesso: {caminho_pdf}")
        
        # Limpeza
        img_capa.close()
        img_p2.close()
        img_template.close()
        try: 
            os.remove(caminho_capa)
            os.remove(caminho_pag2)
        except: pass

    except Exception as e:
        print(f"   ❌ Erro ao gerar PDF vazio: {e}")

def gerar_capa(nome_cliente, texto_periodo, pasta_saida, pasta_raiz):
    # Configurações da Capa
    width = 1920
    height = 1080
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    azul_cx = (0, 51, 102)
    preto = (0, 0, 0)
    cinza = (100, 100, 100)

    # Tenta carregar logo
    possiveis_logos = ["cxtrade_logo.jpg", "logo_cx.png", "logo_cx.jpg"]
    caminho_logo = None
    for nome in possiveis_logos:
        temp = os.path.join(pasta_raiz, nome)
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
    texto_cli = f"CLIENTE: {nome_cliente}"
    texto_gerado = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"

    def draw_center(txt, fnt, y, cor):
        try:
            bb = draw.textbbox((0,0), txt, font=fnt)
            w = bb[2]-bb[0]
        except: w = draw.textlength(txt, font=fnt)
        draw.text(((width-w)/2, y), txt, font=fnt, fill=cor)

    start_y = top_margin_logo + logo_height + 100 if logo_height > 0 else 300
    
    draw_center(texto_titulo, f_tit, start_y, azul_cx)
    draw_center(texto_cli, f_cli, start_y + 180, preto)
    draw_center(f"Período: {texto_periodo}", f_dat, start_y + 350, cinza)
    draw_center(texto_gerado, f_dat, start_y + 430, cinza)

    path = os.path.join(pasta_saida, f"capa_temp_{nome_cliente}.png")
    img.save(path)
    return path