# main.py (versão com correção no leitor de log)
import subprocess
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

SRC_DIR = os.path.join(BASE_DIR, "src")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"log_{timestamp}.txt"
log_filepath = os.path.join(LOG_DIR, log_filename)

def enviar_email_de_erro(log_content, erro_msg):
    print("\nINFO: Tentando enviar notificacao de erro por e-mail...")
    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        from_email = os.getenv("GOOGLE_EMAIL")
        password = os.getenv("GOOGLE_PASSWORD")
        to_email = os.getenv("NOTIFY_EMAIL_TO")

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"ERRO: Falha na Automacao de Relatorios CX ({timestamp})"
        body = f"A automacao de relatorios falhou em {datetime.now().strftime('%d/%m/%Y as %H:%M:%S')}.\n\nErro principal: {erro_msg}\n\nAbaixo esta o log completo:\n----------------------------------------------------\n\n{log_content}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email.split(','), msg.as_string())
        server.quit()
        print("INFO: E-mail de notificacao enviado com sucesso.")
    except Exception as e:
        print(f"ERRO: Falha ao enviar o e-mail de notificacao: {e}")

scripts = ["limpar_arquivos.py", "deletar_fotos_minio.py", "processar_email.py", "salvar_minio.py"]
print(f"==> Iniciando pipeline. Log sera salvo em: {log_filepath}")

try:
    with open(log_filepath, 'a', encoding='utf-8') as log_file:
        log_file.write(f"Pipeline iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "="*50 + "\n")
        
        for script in scripts:
            caminho = os.path.join(SRC_DIR, script)
            mensagem_execucao = f"\n--> Executando: {script}\n"
            print(mensagem_execucao)
            log_file.write(mensagem_execucao)
            log_file.flush()

            subprocess.run([sys.executable, caminho], check=True, stdout=log_file, stderr=log_file)
            
            mensagem_sucesso = f"--> Finalizado: {script}\n"
            print(mensagem_sucesso)
            log_file.write(mensagem_sucesso)
            log_file.flush()
        
        mensagem_final = "\n==> Pipeline finalizado com sucesso!\n"
        print(mensagem_final)
        log_file.write("="*50 + "\n" + mensagem_final)

except subprocess.CalledProcessError as e:
    mensagem_erro = f"\n!!! ERRO FATAL ao executar {os.path.basename(e.cmd[-1])}: O pipeline foi interrompido.\n"
    print(mensagem_erro)
    
    with open(log_filepath, 'a', encoding='utf-8') as log_file:
        log_file.write(mensagem_erro)
    
    # --- ALTERAÇÃO PRINCIPAL AQUI ---
    # Adicionamos 'errors='ignore'' para evitar o erro de decodificação
    with open(log_filepath, 'r', encoding='utf-8', errors='ignore') as log_file:
        log_content_completo = log_file.read()
    
    enviar_email_de_erro(log_content_completo, str(e))
    
    print("\n==> Pipeline finalizado COM ERROS!")
    sys.exit(e.returncode)