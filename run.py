#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar o servidor da aplicação Vortex Catálogo.
Inclui verificações de pré-requisitos e configurações.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import platform
import webbrowser
import threading
import time

# Verificar versão do Python
if sys.version_info < (3, 7):
    print("ERRO: Python 3.7 ou superior é necessário.")
    sys.exit(1)

# Tentar importar Flask para verificar se está instalado
try:
    import flask
    print(f"✓ Flask {flask.__version__} encontrado")
except ImportError:
    print("ERRO: Flask não está instalado. Execute 'pip install -r requirements.txt'")
    sys.exit(1)

# Tentar importar Bcrypt para verificar se está instalado
try:
    import bcrypt
    print("✓ Bcrypt encontrado")
except ImportError:
    print("ERRO: Bcrypt não está instalado. Execute 'pip install -r requirements.txt'")
    sys.exit(1)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar diretório de trabalho
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Verificar arquivos essenciais
arquivos_essenciais = ['app.py', 'main.py', 'utils.py']
for arquivo in arquivos_essenciais:
    if not os.path.exists(arquivo):
        print(f"ERRO: Arquivo {arquivo} não encontrado!")
        sys.exit(1)
    print(f"✓ Arquivo {arquivo} encontrado")

# Verificar diretórios
diretorios = ['templates', 'static']
for diretorio in diretorios:
    if not os.path.isdir(diretorio):
        print(f"ERRO: Diretório {diretorio} não encontrado!")
        sys.exit(1)
    print(f"✓ Diretório {diretorio} encontrado")

# Garantir que o diretório static/images existe
if not os.path.isdir('static/images'):
    print("! Criando diretório static/images...")
    os.makedirs('static/images', exist_ok=True)

# Função para abrir o navegador após um delay
def abrir_navegador():
    time.sleep(2)  # Aguardar 2 segundos para o servidor iniciar
    url = "http://localhost:5000"
    print(f"\nAbrindo navegador em {url}...")
    webbrowser.open(url)

# Configurações de acordo com o sistema operacional
def exibir_info_sistema():
    print("\nInformações do Sistema:")
    print(f"Sistema: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Diretório: {os.getcwd()}")
    print(f"Modo: {'Desenvolvimento' if os.getenv('FLASK_ENV') == 'development' else 'Produção'}")

def iniciar_servidor():
    print("\n" + "="*50)
    print(" Vortex Catálogo - Servidor Web ".center(50, "="))
    print("="*50 + "\n")
    
    exibir_info_sistema()
    
    print("\nIniciando servidor...")
    
    # Verificar se é um reinício do servidor (não perguntar novamente no reinício)
    # WERKZEUG_RUN_MAIN é definido quando o app é reiniciado pelo modo debug
    eh_reinicio = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    # Verificar se deve abrir o navegador automaticamente, apenas na primeira execução
    if not eh_reinicio:
        abrir_browser = input("\nDeseja abrir o navegador automaticamente? (S/n): ").lower() != 'n'
        
        if abrir_browser:
            # Iniciar thread para abrir o navegador após o servidor iniciar
            threading.Thread(target=abrir_navegador).start()
    
    # Iniciar o servidor
    print("\nServidor iniciando... Pressione Ctrl+C para encerrar.\n")
    
    # Importar a aplicação
    from app import app
    
    # Definir host e porta
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Iniciar o servidor
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    iniciar_servidor() 