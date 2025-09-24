# src/processar_email.py (versão final sem emojis)
import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import fitz  # PyMuPDF

# --- Configuração ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path=dotenv_path)

DOWNLOAD_PDF_DIR = os.path.join(PROJECT_ROOT, "downloads", "pdfs")
OUTPUT_FOTOS_DIR = os.path.join(PROJECT_ROOT, "fotos")

IMAP_SERVER = "imap.gmail.com"
EMAIL_LOGIN = os.getenv("GOOGLE_EMAIL")
EMAIL_APP_PASSWORD = os.getenv("GOOGLE_PASSWORD")
EMAIL_SENDER = "looker-studio-noreply@google.com"
EMAIL_SUBJECT = "GERAL (CX)"

# --- Funções do Script ---

def converter_pdf_para_jpeg(caminho_pdf, pasta_saida):
    """Converte a primeira página de um PDF para uma imagem JPEG."""
    try:
        nome_arquivo = os.path.basename(caminho_pdf).replace('.pdf', '')
        caminho_jpeg = os.path.join(pasta_saida, f"{nome_arquivo}.jpeg")
        
        doc = fitz.open(caminho_pdf)
        pagina = doc.load_page(0)
        pix = pagina.get_pixmap(dpi=200)
        
        pix.save(caminho_jpeg)
        doc.close()
        print(f"INFO: PDF convertido para JPEG: {caminho_jpeg}")
        return caminho_jpeg
    except Exception as e:
        print(f"ERRO: Erro ao converter PDF: {e}")
        return None

def processar_email():
    """Conecta ao e-mail, baixa o anexo PDF e o converte para imagem."""
    os.makedirs(DOWNLOAD_PDF_DIR, exist_ok=True)
    os.makedirs(OUTPUT_FOTOS_DIR, exist_ok=True)

    imap_connection = None
    try:
        # Linhas corrigidas - sem emojis
        print("INFO: Conectando ao servidor de e-mail...")
        imap_connection = imaplib.IMAP4_SSL(IMAP_SERVER)
        imap_connection.login(EMAIL_LOGIN, EMAIL_APP_PASSWORD)
        imap_connection.select("inbox")
        print("INFO: Conectado e caixa de entrada selecionada.")

        search_criteria = f'(UNSEEN FROM "{EMAIL_SENDER}" SUBJECT "{EMAIL_SUBJECT}")'
        status, messages = imap_connection.search(None, search_criteria)
        
        if status != "OK" or not messages[0]:
            print("AVISO: Nenhum e-mail novo do Looker Studio encontrado.")
            return

        latest_email_id = messages[0].split()[-1]
        print(f"INFO: E-mail encontrado, processando...")

        status, msg_data = imap_connection.fetch(latest_email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                for part in msg.walk():
                    if "attachment" in str(part.get("Content-Disposition")):
                        filename = part.get_filename()
                        if filename and filename.lower().endswith(".pdf"):
                            caminho_pdf = os.path.join(DOWNLOAD_PDF_DIR, filename)
                            with open(caminho_pdf, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            print(f"INFO: Anexo PDF baixado: {caminho_pdf}")
                            
                            converter_pdf_para_jpeg(caminho_pdf, OUTPUT_FOTOS_DIR)
                            return
        
        print("AVISO: E-mail encontrado, mas nenhum anexo PDF foi localizado.")

    except Exception as e:
        # Linha corrigida - sem emoji
        print(f"ERRO: Erro no processamento do e-mail: {e}")
    finally:
        if imap_connection:
            imap_connection.close()
            imap_connection.logout()
            print("INFO: Conexao com o e-mail fechada.")

if __name__ == "__main__":
    processar_email()