#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar senhas dos usuários do formato antigo (hash SHA256) para bcrypt.
Deve ser executado uma única vez durante a atualização do sistema.
"""

import json
import os
import sys
import logging
import hashlib
import bcrypt
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migracao_senhas.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Definir caminho do arquivo de usuários
USUARIOS_FILE = 'usuarios.json'

def hash_password(password):
    """Gera um hash seguro para a senha usando bcrypt"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verificar_senha_antiga(senha, senha_hash):
    """Verifica a senha usando o método antigo (SHA256)"""
    salt = senha_hash[:32]
    senha_hash_calculado = salt + hashlib.sha256(salt.encode() + senha.encode()).hexdigest()
    return senha_hash_calculado == senha_hash

def migrar_senhas():
    """Migrar senhas do formato antigo para bcrypt"""
    logger.info("Iniciando migração de senhas...")
    
    # Verificar se o arquivo existe
    if not os.path.exists(USUARIOS_FILE):
        logger.error(f"Arquivo {USUARIOS_FILE} não encontrado!")
        return False
    
    try:
        # Carregar dados de usuários
        with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        if 'usuarios' not in dados:
            logger.error("Formato de arquivo inválido: chave 'usuarios' não encontrada!")
            return False
        
        total_usuarios = len(dados['usuarios'])
        usuarios_migrados = 0
        
        logger.info(f"Total de {total_usuarios} usuários encontrados para migração.")
        
        # Senhas para teste de migração por usuário
        # Isso permite verificar e migrar mesmo sem conhecer as senhas reais
        senhas_teste = {
            "admin@vortex.com": "admin123",  # Senha do admin padrão
            # Adicione outras senhas conhecidas para usuários específicos
        }
        
        # Processar cada usuário
        for usuario in dados['usuarios']:
            logger.info(f"Processando usuário: {usuario.get('nome')} ({usuario.get('email')})")
            
            # Verificar se já é bcrypt (começa com $2b$)
            if usuario['senha_hash'].startswith('$2b$'):
                logger.info(f"Usuário {usuario['email']} já possui senha no formato bcrypt. Ignorando.")
                continue
            
            # Tratar usuários com senhas conhecidas (testes)
            email = usuario.get('email')
            if email in senhas_teste:
                senha_teste = senhas_teste[email]
                if verificar_senha_antiga(senha_teste, usuario['senha_hash']):
                    # Migrar senha
                    novo_hash = hash_password(senha_teste)
                    usuario['senha_hash'] = novo_hash
                    logger.info(f"Senha do usuário {email} migrada com sucesso!")
                    usuarios_migrados += 1
                else:
                    logger.warning(f"Senha de teste para {email} não confere. Usando senha padrão para migração.")
                    # Definir uma senha padrão para reset
                    novo_hash = hash_password("Vortex@2025")
                    usuario['senha_hash'] = novo_hash
                    logger.info(f"Senha do usuário {email} definida para padrão (Vortex@2025)")
                    usuarios_migrados += 1
            else:
                # Para usuários sem senha conhecida, definir senha padrão
                logger.warning(f"Usuário {email} sem senha conhecida. Usando senha padrão para migração.")
                novo_hash = hash_password("Vortex@2025")
                usuario['senha_hash'] = novo_hash
                logger.info(f"Senha do usuário {email} definida para padrão (Vortex@2025)")
                usuarios_migrados += 1
        
        # Salvar alterações
        with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Migração concluída! {usuarios_migrados} de {total_usuarios} usuários migrados.")
        return True
    
    except Exception as e:
        logger.error(f"Erro durante a migração: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def fazer_backup():
    """Cria um backup do arquivo de usuários antes da migração"""
    if os.path.exists(USUARIOS_FILE):
        backup_file = f"{USUARIOS_FILE}.bak.{int(time.time())}"
        try:
            with open(USUARIOS_FILE, 'r', encoding='utf-8') as f_in:
                with open(backup_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())
            logger.info(f"Backup criado em {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}")
            return False
    else:
        logger.warning(f"Arquivo {USUARIOS_FILE} não encontrado para backup!")
        return False

if __name__ == "__main__":
    print("Migração de Senhas - Vortex Catálogo")
    print("===================================")
    print("Este script irá migrar as senhas dos usuários para um formato mais seguro.")
    print("As senhas que não puderem ser migradas serão definidas como 'Vortex@2025'.")
    print("\nATENÇÃO: Certifique-se de que o sistema não está em uso durante a migração!")
    print("Recomenda-se fazer um backup antes de continuar.")
    
    resposta = input("\nDeseja continuar com a migração? (s/N): ")
    if resposta.lower() != 's':
        print("Migração cancelada.")
        sys.exit(0)
    
    # Criar backup
    print("\nCriando backup...")
    if fazer_backup():
        print("Backup criado com sucesso!")
    else:
        resposta = input("Falha ao criar backup. Deseja continuar mesmo assim? (s/N): ")
        if resposta.lower() != 's':
            print("Migração cancelada.")
            sys.exit(0)
    
    # Executar migração
    print("\nIniciando migração de senhas...")
    if migrar_senhas():
        print("\nMigração concluída com sucesso!")
        print("Todos os usuários podem fazer login com 'Vortex@2025' caso suas senhas não tenham sido migradas corretamente.")
    else:
        print("\nFalha na migração! Verifique o arquivo migracao_senhas.log para mais detalhes.")
    
    print("\nPressione Enter para sair...")
    input() 