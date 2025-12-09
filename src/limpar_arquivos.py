# src/limpar_arquivos.py
import os
import shutil

PASTAS_PARA_LIMPAR = ["downloads", "fotos",]

def limpar_pasta(caminho_pasta):
    if not os.path.isdir(caminho_pasta):
        print(f"AVISO: Pasta nao encontrada, pulando limpeza: {caminho_pasta}")
        return
        
    for nome_arquivo in os.listdir(caminho_pasta):
        caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)
        try:
            if os.path.isfile(caminho_arquivo) or os.path.islink(caminho_arquivo):
                os.unlink(caminho_arquivo)
            elif os.path.isdir(caminho_arquivo):
                shutil.rmtree(caminho_arquivo)
        except Exception as e:
            print(f'ERRO: Falha ao deletar {caminho_arquivo}. Razao: {e}')
    # Linha corrigida - sem emoji
    print(f"INFO: Pasta '{caminho_pasta}' limpa com sucesso.")

if __name__ == "__main__":
    print("Iniciando limpeza das pastas de trabalho...")
    for pasta in PASTAS_PARA_LIMPAR:
        caminho_completo = os.path.join(os.path.dirname(__file__), '..', pasta)
        limpar_pasta(caminho_completo)
    print("INFO: Limpeza finalizada.")