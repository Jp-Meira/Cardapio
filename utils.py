#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
import bcrypt
import secrets
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Configura logger com rotação de arquivo
def setup_logger(name, log_file, level=logging.INFO, max_size=10*1024*1024, backup_count=5):
    """Configura um logger com rotação de arquivo para evitar arquivos de log enormes"""
    handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    # Adiciona handler para console
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    return logger

# Funções de hash seguras para senhas
def hash_password(password):
    """Gera um hash seguro para a senha usando bcrypt"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed):
    """Verifica se a senha corresponde ao hash armazenado"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password, hashed)

def generate_token():
    """Gera um token seguro para redefinição de senha"""
    return secrets.token_urlsafe(32)

# Funções de validação
def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validar_telefone(telefone):
    """Valida formato de telefone (aceita qualquer formato, incluindo números curtos)"""
    # Remove caracteres não numéricos
    numero = re.sub(r'\D', '', telefone)
    # Verifica se tem pelo menos 2 dígitos (aceitando qualquer formato)
    return len(numero) >= 2

# Funções para formatar datas
def formatar_data(dt=None):
    """Formata data em formato brasileiro (dd/mm/aaaa HH:MM:SS)"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%d/%m/%Y %H:%M:%S")

def parse_data_br(data_str):
    """Converte string de data no formato brasileiro para objeto datetime"""
    try:
        return datetime.strptime(data_str, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        return None

# Funções para carregar e salvar dados (cache de arquivos)
_cache = {}

def carregar_json_com_cache(arquivo, tempo_cache=60):
    """Carrega um arquivo JSON com cache para evitar I/O excessivo"""
    import json
    import time
    
    agora = time.time()
    
    # Se o arquivo estiver em cache e for recente, retorna do cache
    if arquivo in _cache and agora - _cache[arquivo]['timestamp'] < tempo_cache:
        return _cache[arquivo]['dados']
    
    # Caso contrário, carrega do disco
    try:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                _cache[arquivo] = {
                    'timestamp': agora,
                    'dados': dados
                }
                return dados
        return {}
    except Exception as e:
        logging.error(f"Erro ao carregar arquivo {arquivo}: {str(e)}")
        return {}

def salvar_json_com_cache(arquivo, dados):
    """Salva dados em um arquivo JSON e atualiza o cache"""
    import json
    import time
    
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            
        # Atualiza o cache
        _cache[arquivo] = {
            'timestamp': time.time(),
            'dados': dados
        }
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar arquivo {arquivo}: {str(e)}")
        return False

# Função para limpar o cache
def limpar_cache(arquivo=None):
    """Limpa o cache para um arquivo específico ou todo o cache"""
    if arquivo:
        if arquivo in _cache:
            del _cache[arquivo]
    else:
        _cache.clear() 