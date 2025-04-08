#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import traceback
import hashlib
import secrets
import re
import time
from utils import hash_password, verify_password, generate_token, formatar_data, validar_email, validar_telefone

# Configuração de logging
logger = logging.getLogger(__name__)

class Produto:
    """
    Classe que representa um produto no catálogo.
    
    Attributes:
        _ultimo_id (int): Contador para gerar IDs sequenciais
        id (str): Identificador único do produto
        nome (str): Nome do produto
        descricao (str): Descrição detalhada do produto
        preco (float): Preço do produto
        quantidade_estoque (int): Quantidade disponível em estoque
        imagem_url (str): URL da imagem do produto
        data_atualizacao (str): Data e hora da última atualização no formato DD/MM/YYYY HH:MM:SS
    """
    _ultimo_id = 0  # Variável de classe para rastrear o último ID usado
    
    def __init__(self, nome, descricao, preco, quantidade_estoque=0, imagem_url=None, id=None, data_atualizacao=None):
        """
        Inicializa um novo produto.
        
        Args:
            nome (str): Nome do produto
            descricao (str): Descrição detalhada do produto
            preco (float): Preço do produto
            quantidade_estoque (int, optional): Quantidade disponível em estoque. Padrão é 0.
            imagem_url (str, optional): URL da imagem do produto. Padrão é None.
            id (str, optional): ID do produto. Se None, gera um novo ID.
            data_atualizacao (str, optional): Data de atualização. Se None, usa a data atual.
        """
        if id is None:
            # Incrementar o contador e usar como ID
            Produto._ultimo_id += 1
            self.id = str(Produto._ultimo_id)
            logger.info(f"Novo produto criado com ID sequencial: {self.id}")
        else:
            self.id = id
            # Atualizar o _ultimo_id se necessário para manter a sequência
            try:
                id_numerico = int(id)
                if id_numerico > Produto._ultimo_id:
                    Produto._ultimo_id = id_numerico
                    logger.info(f"_ultimo_id atualizado para: {Produto._ultimo_id}")
            except ValueError:
                # Se não for um ID numérico, não afeta o _ultimo_id
                logger.warning(f"ID não numérico fornecido: {id}")
                pass
                
        self.nome = nome
        self.descricao = descricao
        self.preco = float(preco)
        self.quantidade_estoque = int(quantidade_estoque)
        self.imagem_url = imagem_url
        self.data_atualizacao = data_atualizacao or formatar_data()
        
    def atualizar_estoque(self, quantidade):
        """
        Atualiza a quantidade em estoque do produto.
        
        Args:
            quantidade (int): Quantidade a ser adicionada (positiva) ou removida (negativa)
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
            
        Raises:
            ValueError: Se a quantidade final ficar negativa
        """
        try:
            nova_quantidade = self.quantidade_estoque + quantidade
            if nova_quantidade < 0:
                logger.warning(f"Tentativa de reduzir estoque abaixo de zero para o produto {self.id} - {self.nome}")
                raise ValueError(f"Estoque insuficiente para o produto {self.nome}. Disponível: {self.quantidade_estoque}, Solicitado: {abs(quantidade)}")
            
            self.quantidade_estoque = nova_quantidade
            self.data_atualizacao = formatar_data()
            logger.info(f"Estoque do produto {self.id} - {self.nome} atualizado para {self.quantidade_estoque}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar estoque do produto {self.id} - {self.nome}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
    def to_dict(self):
        """
        Converte o produto em um dicionário.
        
        Returns:
            dict: Representação do produto em dicionário
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': self.preco,
            'quantidade_estoque': self.quantidade_estoque,
            'imagem_url': self.imagem_url,
            'data_atualizacao': self.data_atualizacao
        }
    
    @classmethod
    def from_dict(cls, dados):
        """
        Cria um produto a partir de um dicionário.
        
        Args:
            dados (dict): Dicionário contendo os dados do produto
            
        Returns:
            Produto: Nova instância do produto
            
        Raises:
            ValueError: Se faltarem campos obrigatórios
        """
        try:
            # Verificar campos obrigatórios
            campos_obrigatorios = ['id', 'nome', 'descricao', 'preco']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    logger.error(f"Campo obrigatório '{campo}' não encontrado nos dados do produto")
                    raise ValueError(f"Campo obrigatório '{campo}' não encontrado nos dados do produto")
                
            produto = cls(
                id=dados['id'],
                nome=dados['nome'],
                descricao=dados['descricao'],
                preco=float(dados['preco']),
                quantidade_estoque=int(dados.get('quantidade_estoque', 0)),
                imagem_url=dados.get('imagem_url'),
                data_atualizacao=dados.get('data_atualizacao')
            )
                
            logger.info(f"Produto carregado de dicionário: {produto.id} - {produto.nome}")
            return produto
        except Exception as e:
            logger.error(f"Erro ao criar produto a partir de dicionário: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Pedido:
    """
    Classe que representa um pedido no sistema.
    
    Attributes:
        _ultimo_id (int): Contador para gerar IDs sequenciais
        id (str): Identificador único do pedido
        produtos (list): Lista de produtos no pedido com suas quantidades
        cliente_nome (str): Nome do cliente
        cliente_telefone (str): Telefone do cliente
        cliente_endereco (str): Endereço de entrega do cliente
        data_pedido (str): Data e hora do pedido no formato DD/MM/YYYY HH:MM:SS
        status (str): Status do pedido (Pendente, Concluído)
    """
    _ultimo_id = 0  # Variável de classe para rastrear o último ID usado
    
    def __init__(self, produtos, cliente_nome, cliente_telefone, cliente_endereco, id=None):
        """
        Inicializa um novo pedido.
        
        Args:
            produtos (list): Lista de produtos no pedido com suas quantidades
            cliente_nome (str): Nome do cliente
            cliente_telefone (str): Telefone do cliente
            cliente_endereco (str): Endereço de entrega do cliente
            id (str, optional): ID do pedido. Se None, gera um novo ID.
        """
        if id is None:
            # Incrementar o contador e usar como ID
            Pedido._ultimo_id += 1
            self.id = str(Pedido._ultimo_id)
            logger.info(f"Novo pedido criado com ID sequencial: {self.id}")
        else:
            self.id = id
            # Atualizar o _ultimo_id se necessário para manter a sequência
            try:
                id_numerico = int(id)
                if id_numerico > Pedido._ultimo_id:
                    Pedido._ultimo_id = id_numerico
                    logger.info(f"_ultimo_id atualizado para: {Pedido._ultimo_id}")
            except ValueError:
                # Se não for um ID numérico, não afeta o _ultimo_id
                logger.warning(f"ID não numérico fornecido: {id}")
                pass
                
        self.produtos = produtos
        self.cliente_nome = cliente_nome
        self.cliente_telefone = cliente_telefone
        self.cliente_endereco = cliente_endereco
        self.data_pedido = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.status = "Pendente"  # Status inicial sempre é Pendente
        
    def to_dict(self):
        """
        Converte o pedido em um dicionário.
        
        Returns:
            dict: Representação do pedido em dicionário
        """
        return {
            'id': self.id,
            'produtos': self.produtos,
            'cliente_nome': self.cliente_nome,
            'cliente_telefone': self.cliente_telefone,
            'cliente_endereco': self.cliente_endereco,
            'data_pedido': self.data_pedido,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, dados):
        """
        Cria um pedido a partir de um dicionário.
        
        Args:
            dados (dict): Dicionário contendo os dados do pedido
            
        Returns:
            Pedido: Nova instância do pedido
            
        Raises:
            ValueError: Se faltarem campos obrigatórios
        """
        try:
            # Verificar campos obrigatórios
            campos_obrigatorios = ['id', 'produtos', 'cliente_nome', 'cliente_telefone', 'cliente_endereco']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    logger.error(f"Campo obrigatório '{campo}' não encontrado nos dados do pedido")
                    raise ValueError(f"Campo obrigatório '{campo}' não encontrado nos dados do pedido")
                
            pedido = cls(
                id=dados['id'],
                produtos=dados['produtos'],
                cliente_nome=dados['cliente_nome'],
                cliente_telefone=dados['cliente_telefone'],
                cliente_endereco=dados['cliente_endereco']
            )
            
            # Preservar a data do pedido e status se existirem
            if 'data_pedido' in dados:
                pedido.data_pedido = dados['data_pedido']
            if 'status' in dados:
                pedido.status = dados['status']
                
            logger.info(f"Pedido carregado de dicionário: {pedido.id} - Cliente: {pedido.cliente_nome}")
            return pedido
        except Exception as e:
            logger.error(f"Erro ao criar pedido a partir de dicionário: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Usuario:
    """
    Classe que representa um usuário do sistema.
    
    Attributes:
        _ultimo_id (int): Contador para gerar IDs sequenciais
        id (str): Identificador único do usuário
        nome (str): Nome completo do usuário
        email (str): Email do usuário
        telefone (str): Telefone do usuário
        senha_hash (str): Hash da senha do usuário usando bcrypt
        reset_token (str): Token para redefinição de senha
        tipo (str): Tipo de usuário (gerente ou funcionario)
        data_criacao (str): Data e hora de criação da conta
    """
    _ultimo_id = 0  # Variável de classe para rastrear o último ID usado
    
    def __init__(self, nome, email, telefone, senha=None, senha_hash=None, tipo="funcionario", id=None, data_criacao=None):
        """
        Inicializa um novo usuário.
        
        Args:
            nome (str): Nome completo do usuário
            email (str): Email do usuário
            telefone (str): Telefone do usuário
            senha (str, optional): Senha em texto puro (será transformada em hash)
            senha_hash (str, optional): Hash da senha (alternativa ao parâmetro senha)
            tipo (str, optional): Tipo de usuário. Padrão é "funcionario"
            id (str, optional): ID do usuário. Se None, gera um novo ID.
            data_criacao (str, optional): Data de criação. Se None, usa a data atual.
        """
        # Validação básica
        if not validar_email(email):
            raise ValueError(f"Email inválido: {email}")
            
        if not validar_telefone(telefone):
            raise ValueError(f"Telefone inválido: {telefone}")
        
        if id is None:
            # Incrementar o contador e usar como ID
            Usuario._ultimo_id += 1
            self.id = str(Usuario._ultimo_id)
            logger.info(f"Novo usuário criado com ID sequencial: {self.id}")
        else:
            self.id = id
            # Atualizar o _ultimo_id se necessário para manter a sequência
            try:
                id_numerico = int(id)
                if id_numerico > Usuario._ultimo_id:
                    Usuario._ultimo_id = id_numerico
                    logger.info(f"_ultimo_id atualizado para: {Usuario._ultimo_id}")
            except ValueError:
                # Se não for um ID numérico, não afeta o _ultimo_id
                logger.warning(f"ID não numérico fornecido: {id}")
                pass
        
        self.nome = nome
        self.email = email
        self.telefone = telefone
        
        # Configuração de senha usando bcrypt
        if senha:
            self.senha_hash = hash_password(senha)
        elif senha_hash:
            self.senha_hash = senha_hash
        else:
            raise ValueError("É necessário fornecer uma senha ou hash de senha")
            
        self.reset_token = None
        self.tipo = tipo
        self.data_criacao = data_criacao or formatar_data()
        
    def verificar_senha(self, senha):
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.
        
        Args:
            senha (str): Senha em texto puro
            
        Returns:
            bool: True se a senha estiver correta, False caso contrário
        """
        return verify_password(senha, self.senha_hash)
        
    def gerar_token_redefinicao(self):
        """
        Gera um token para redefinição de senha.
        
        Returns:
            str: Token de redefinição
        """
        self.reset_token = generate_token()
        return self.reset_token
        
    def limpar_token_redefinicao(self):
        """
        Limpa o token de redefinição de senha.
        """
        self.reset_token = None
        
    def atualizar_senha(self, nova_senha):
        """
        Atualiza a senha do usuário.
        
        Args:
            nova_senha (str): Nova senha em texto puro
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        self.senha_hash = hash_password(nova_senha)
        self.limpar_token_redefinicao()
        return True
        
    def to_dict(self):
        """
        Converte o usuário em um dicionário.
        
        Returns:
            dict: Representação do usuário em dicionário
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'senha_hash': self.senha_hash,
            'reset_token': self.reset_token,
            'tipo': self.tipo,
            'data_criacao': self.data_criacao
        }
    
    @classmethod
    def from_dict(cls, dados):
        """
        Cria um usuário a partir de um dicionário.
        
        Args:
            dados (dict): Dicionário contendo os dados do usuário
            
        Returns:
            Usuario: Nova instância do usuário
            
        Raises:
            ValueError: Se faltarem campos obrigatórios
        """
        try:
            # Verificar campos obrigatórios
            campos_obrigatorios = ['id', 'nome', 'email', 'telefone', 'senha_hash', 'tipo']
            for campo in campos_obrigatorios:
                if campo not in dados:
                    logger.error(f"Campo obrigatório '{campo}' não encontrado nos dados do usuário")
                    raise ValueError(f"Campo obrigatório '{campo}' não encontrado nos dados do usuário")
                
            usuario = cls(
                id=dados['id'],
                nome=dados['nome'],
                email=dados['email'],
                telefone=dados['telefone'],
                senha_hash=dados['senha_hash'],
                tipo=dados['tipo'],
                data_criacao=dados.get('data_criacao')
            )
            
            # Campos opcionais
            if 'reset_token' in dados:
                usuario.reset_token = dados['reset_token']
                
            logger.info(f"Usuário carregado de dicionário: {usuario.id} - {usuario.nome}")
            return usuario
        except Exception as e:
            logger.error(f"Erro ao criar usuário a partir de dicionário: {str(e)}")
            logger.error(traceback.format_exc())
            raise

class Catalogo:
    """
    Classe que gerencia o catálogo de produtos e pedidos do sistema.
    
    Attributes:
        produtos (list): Lista de produtos no catálogo
        pedidos (list): Lista de pedidos realizados
        usuarios (list): Lista de usuários do sistema
    """
    
    def __init__(self):
        """
        Inicializa um novo catálogo.
        """
        logger.info("Inicializando novo catálogo")
        self.produtos = []
        self.pedidos = []
        self.usuarios = []
    
    def _atualizar_indices(self):
        """
        Atualiza os índices internos do catálogo.
        Esta função é chamada automaticamente após carregar produtos, pedidos e usuários.
        """
        # Atualizar índice de ID de produtos
        if self.produtos:
            try:
                ids_numericos = [int(p.id) for p in self.produtos if p.id.isdigit()]
                if ids_numericos:
                    Produto._ultimo_id = max(ids_numericos)
                    logger.info(f"Índice de produtos atualizado para: {Produto._ultimo_id}")
            except Exception as e:
                logger.error(f"Erro ao atualizar índice de produtos: {e}")
        
        # Atualizar índice de ID de pedidos
        if self.pedidos:
            try:
                ids_numericos = [int(p.id) for p in self.pedidos if p.id.isdigit()]
                if ids_numericos:
                    Pedido._ultimo_id = max(ids_numericos)
                    logger.info(f"Índice de pedidos atualizado para: {Pedido._ultimo_id}")
            except Exception as e:
                logger.error(f"Erro ao atualizar índice de pedidos: {e}")
        
        # Atualizar índice de ID de usuários
        if self.usuarios:
            try:
                ids_numericos = [int(u.id) for u in self.usuarios if u.id.isdigit()]
                if ids_numericos:
                    Usuario._ultimo_id = max(ids_numericos)
                    logger.info(f"Índice de usuários atualizado para: {Usuario._ultimo_id}")
            except Exception as e:
                logger.error(f"Erro ao atualizar índice de usuários: {e}")
    
    def adicionar_produto(self, nome, descricao, preco, quantidade_estoque=0, imagem_url=None):
        """
        Adiciona um novo produto ao catálogo.
        
        Args:
            nome (str): Nome do produto
            descricao (str): Descrição detalhada do produto
            preco (float): Preço do produto
            quantidade_estoque (int, optional): Quantidade disponível em estoque. Padrão é 0.
            imagem_url (str, optional): URL da imagem do produto. Padrão é None.
            
        Returns:
            Produto: O produto adicionado
            
        Raises:
            ValueError: Se algum parâmetro for inválido
        """
        try:
            # Validações
            if not nome or not isinstance(nome, str):
                logger.error("Nome do produto inválido")
                raise ValueError("Nome do produto é obrigatório e deve ser uma string")
                
            if not descricao or not isinstance(descricao, str):
                logger.error("Descrição do produto inválida")
                raise ValueError("Descrição do produto é obrigatória e deve ser uma string")
                
            try:
                preco = float(preco)
                if preco < 0:
                    logger.error(f"Preço do produto inválido: {preco}")
                    raise ValueError("Preço do produto deve ser maior ou igual a zero")
            except (ValueError, TypeError):
                logger.error(f"Erro ao converter preço do produto: {preco}")
                raise ValueError("Preço do produto deve ser um número válido")
                
            try:
                quantidade_estoque = int(quantidade_estoque)
                if quantidade_estoque < 0:
                    logger.error(f"Quantidade em estoque inválida: {quantidade_estoque}")
                    raise ValueError("Quantidade em estoque deve ser maior ou igual a zero")
            except (ValueError, TypeError):
                logger.error(f"Erro ao converter quantidade em estoque: {quantidade_estoque}")
                raise ValueError("Quantidade em estoque deve ser um número inteiro válido")
            
            produto = Produto(nome, descricao, preco, quantidade_estoque, imagem_url)
            self.produtos.append(produto)
            logger.info(f"Produto adicionado ao catálogo: {produto.id} - {produto.nome}")
            return produto.to_dict()
        except Exception as e:
            logger.error(f"Erro ao adicionar produto: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def remover_produto(self, produto_id):
        """
        Remove um produto do catálogo pelo ID.
        
        Args:
            produto_id (str): ID do produto a ser removido
            
        Returns:
            bool: True se o produto foi removido, False se não foi encontrado
            
        Raises:
            ValueError: Se o produto estiver em pedidos pendentes
        """
        try:
            # Encontrar o produto pelo ID
            produto = next((p for p in self.produtos if p.id == produto_id), None)
            
            if not produto:
                logger.warning(f"Tentativa de remover produto inexistente: {produto_id}")
                return False
            
            # Verificar se o produto está em algum pedido pendente
            for pedido in self.pedidos:
                if pedido.status == 'Pendente':
                    for item in pedido.produtos:
                        if item['id'] == produto_id:
                            logger.warning(f"Tentativa de remover produto {produto_id} que está em pedidos pendentes")
                            raise ValueError("Este produto está em pedidos pendentes e não pode ser removido")
            
            # Remover o produto
            self.produtos.remove(produto)
            logger.info(f"Produto removido do catálogo: {produto_id} - {produto.nome}")
            return True
        except Exception as e:
            if isinstance(e, ValueError):
                # Repassar erros de validação
                raise
            logger.error(f"Erro ao remover produto {produto_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def atualizar_produto(self, produto_id, **kwargs):
        """
        Atualiza um produto existente no catálogo.
        
        Args:
            produto_id (str): ID do produto a ser atualizado
            **kwargs: Atributos a serem atualizados (nome, descricao, preco, quantidade_estoque, imagem_url)
            
        Returns:
            Produto: O produto atualizado
            
        Raises:
            ValueError: Se o produto não for encontrado ou se algum valor for inválido
        """
        try:
            # Encontrar o produto pelo ID
            produto = next((p for p in self.produtos if p.id == produto_id), None)
            
            if not produto:
                logger.warning(f"Tentativa de atualizar produto inexistente: {produto_id}")
                raise ValueError(f"Produto com ID {produto_id} não encontrado")
            
            # Atualizar atributos
            if 'nome' in kwargs and kwargs['nome']:
                produto.nome = kwargs['nome']
                
            if 'descricao' in kwargs and kwargs['descricao']:
                produto.descricao = kwargs['descricao']
                
            if 'preco' in kwargs:
                try:
                    preco = float(kwargs['preco'])
                    if preco < 0:
                        raise ValueError("Preço deve ser maior ou igual a zero")
                    produto.preco = preco
                except (ValueError, TypeError):
                    logger.error(f"Erro ao converter preço do produto: {kwargs['preco']}")
                    raise ValueError("Preço deve ser um número válido")
                    
            if 'quantidade_estoque' in kwargs:
                try:
                    quantidade = int(kwargs['quantidade_estoque'])
                    if quantidade < 0:
                        raise ValueError("Quantidade em estoque deve ser maior ou igual a zero")
                    produto.quantidade_estoque = quantidade
                except (ValueError, TypeError):
                    logger.error(f"Erro ao converter quantidade em estoque: {kwargs['quantidade_estoque']}")
                    raise ValueError("Quantidade em estoque deve ser um número inteiro válido")
                    
            if 'imagem_url' in kwargs:
                produto.imagem_url = kwargs['imagem_url']
            
            # Atualizar data de atualização
            produto.data_atualizacao = formatar_data()
            
            logger.info(f"Produto atualizado: {produto_id} - {produto.nome}")
            return produto.to_dict()
        except Exception as e:
            if isinstance(e, ValueError):
                # Repassar erros de validação
                raise
            logger.error(f"Erro ao atualizar produto {produto_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def obter_produto(self, produto_id):
        """
        Obtém um produto pelo ID.
        
        Args:
            produto_id (str): ID do produto
            
        Returns:
            Produto: O produto encontrado ou None se não for encontrado
        """
        try:
            produto = next((p for p in self.produtos if p.id == produto_id), None)
            if produto:
                logger.info(f"Produto encontrado: {produto_id} - {produto.nome}")
                return produto.to_dict()
            else:
                logger.warning(f"Produto não encontrado: {produto_id}")
                return None
        except Exception as e:
            logger.error(f"Erro ao obter produto {produto_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def listar_produtos(self):
        """
        Lista todos os produtos do catálogo.
        
        Returns:
            list: Lista de dicionários representando os produtos
        """
        try:
            produtos_dict = [p.to_dict() for p in self.produtos]
            logger.info(f"Listando {len(produtos_dict)} produtos")
            return produtos_dict
        except Exception as e:
            logger.error(f"Erro ao listar produtos: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def criar_pedido(self, produtos, cliente_nome, cliente_telefone, cliente_endereco):
        """
        Cria um novo pedido e atualiza o estoque dos produtos.
        
        Args:
            produtos (list): Lista de dicionários com 'id' e 'quantidade' dos produtos
            cliente_nome (str): Nome do cliente
            cliente_telefone (str): Telefone do cliente
            cliente_endereco (str): Endereço de entrega do cliente
            
        Returns:
            Pedido: O pedido criado
            
        Raises:
            ValueError: Se algum produto não for encontrado ou não houver estoque suficiente
        """
        try:
            # Validações
            if not produtos or not isinstance(produtos, list):
                logger.error("Lista de produtos inválida")
                raise ValueError("Lista de produtos é obrigatória e deve ser uma lista")
                
            if not cliente_nome or not isinstance(cliente_nome, str):
                logger.error("Nome do cliente inválido")
                raise ValueError("Nome do cliente é obrigatório e deve ser uma string")
                
            if not cliente_telefone or not isinstance(cliente_telefone, str):
                logger.error("Telefone do cliente inválido")
                raise ValueError("Telefone do cliente é obrigatório e deve ser uma string")
                
            if not cliente_endereco or not isinstance(cliente_endereco, str):
                logger.error("Endereço do cliente inválido")
                raise ValueError("Endereço do cliente é obrigatório e deve ser uma string")
            
            # Verificar e atualizar estoque
            for item in produtos:
                if 'id' not in item or 'quantidade' not in item:
                    logger.error("Item do pedido com formato inválido")
                    raise ValueError("Formato de produto inválido. Necessário id e quantidade")
                    
                produto = next((p for p in self.produtos if p.id == item['id']), None)
                if not produto:
                    logger.error(f"Produto com ID {item['id']} não encontrado para o pedido")
                    raise ValueError(f"Produto com ID {item['id']} não encontrado")
                    
                if produto.quantidade_estoque < item['quantidade']:
                    logger.error(f"Estoque insuficiente para o produto {produto.nome} (ID: {produto.id}). Solicitado: {item['quantidade']}, Disponível: {produto.quantidade_estoque}")
                    raise ValueError(f"Produto {produto.nome} não possui estoque suficiente. Disponível: {produto.quantidade_estoque}")
            
            # Criar o pedido
            produtos_info = []
            for item in produtos:
                produto = next((p for p in self.produtos if p.id == item['id']), None)
                # Armazenar todas as informações relevantes do produto no momento do pedido
                produtos_info.append({
                    'id': item['id'],
                    'quantidade': item['quantidade'],
                    'nome': produto.nome,
                    'preco': produto.preco,
                    'descricao': produto.descricao,
                    'imagem_url': produto.imagem_url
                })
                
                # Atualizar estoque
                produto.atualizar_estoque(-item['quantidade'])
            
            pedido = Pedido(produtos_info, cliente_nome, cliente_telefone, cliente_endereco)
            self.pedidos.append(pedido)
            
            logger.info(f"Pedido criado: {pedido.id} - Cliente: {cliente_nome} - Produtos: {len(produtos_info)}")
            return pedido.to_dict()
        except Exception as e:
            if isinstance(e, ValueError):
                # Repassar erros de validação
                raise
            logger.error(f"Erro ao criar pedido: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def listar_pedidos(self):
        """
        Lista todos os pedidos.
        
        Returns:
            list: Lista de dicionários representando os pedidos
        """
        try:
            pedidos_dict = [p.to_dict() for p in self.pedidos]
            logger.info(f"Listando {len(pedidos_dict)} pedidos")
            return pedidos_dict
        except Exception as e:
            logger.error(f"Erro ao listar pedidos: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def obter_pedido(self, pedido_id):
        """
        Obtém um pedido pelo ID.
        
        Args:
            pedido_id (str): ID do pedido
            
        Returns:
            Pedido: O pedido encontrado ou None se não for encontrado
        """
        try:
            pedido = next((p for p in self.pedidos if p.id == pedido_id), None)
            if pedido:
                logger.info(f"Pedido encontrado: {pedido_id} - Cliente: {pedido.cliente_nome}")
                return pedido.to_dict()
            else:
                logger.warning(f"Pedido não encontrado: {pedido_id}")
                return None
        except Exception as e:
            logger.error(f"Erro ao obter pedido {pedido_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def atualizar_status_pedido(self, pedido_id, novo_status):
        """
        Atualiza o status de um pedido.
        
        Args:
            pedido_id (str): ID do pedido
            novo_status (str): Novo status do pedido
            
        Returns:
            Pedido: O pedido atualizado
            
        Raises:
            ValueError: Se o pedido não for encontrado ou o status for inválido
        """
        try:
            # Verificar status válido
            status_validos = ['Pendente', 'Concluído']
            if novo_status not in status_validos:
                logger.error(f"Status inválido: {novo_status}")
                raise ValueError(f"Status inválido. Status válidos são: {', '.join(status_validos)}")
            
            # Encontrar o pedido pelo ID
            pedido = next((p for p in self.pedidos if p.id == pedido_id), None)
            if not pedido:
                logger.warning(f"Tentativa de atualizar status de pedido inexistente: {pedido_id}")
                raise ValueError(f"Pedido com ID {pedido_id} não encontrado")
            
            # Atualizar status
            pedido.status = novo_status
            logger.info(f"Status do pedido {pedido_id} atualizado para: {novo_status}")
            
            return pedido.to_dict()
        except Exception as e:
            if isinstance(e, ValueError):
                # Repassar erros de validação
                raise
            logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def adicionar_usuario(self, nome, email, telefone, senha, tipo="funcionario"):
        """
        Adiciona um novo usuário ao sistema.
        
        Args:
            nome (str): Nome completo do usuário
            email (str): Email do usuário
            telefone (str): Telefone do usuário
            senha (str): Senha em texto puro
            tipo (str, optional): Tipo de usuário. Padrão é "funcionario"
            
        Returns:
            Usuario: O usuário criado
            
        Raises:
            ValueError: Se o email ou telefone já estiverem em uso
        """
        try:
            # Validar email
            if not validar_email(email):
                raise ValueError("Email inválido")
                
            # Verificar se email ou telefone já existem
            for usuario in self.usuarios:
                if usuario.email == email:
                    raise ValueError("Email já cadastrado")
                if usuario.telefone == telefone:
                    raise ValueError("Telefone já cadastrado")
            
            # Criar novo usuário
            novo_usuario = Usuario(nome=nome, email=email, telefone=telefone, senha=senha, tipo=tipo)
            self.usuarios.append(novo_usuario)
            
            logger.info(f"Novo usuário adicionado: {novo_usuario.id} - {novo_usuario.nome} ({novo_usuario.tipo})")
            return novo_usuario.to_dict()
        except Exception as e:
            logger.error(f"Erro ao adicionar usuário: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def obter_usuario_por_id(self, usuario_id):
        """
        Obtém um usuário pelo ID.
        
        Args:
            usuario_id (str): ID do usuário
            
        Returns:
            Usuario: O usuário encontrado ou None
        """
        try:
            logger.info(f"Tentando obter usuário por ID: {usuario_id}")
            logger.info(f"Total de usuários no catálogo: {len(self.usuarios)}")
            
            usuarios_ids = [u.id for u in self.usuarios]
            logger.info(f"IDs de usuários disponíveis: {usuarios_ids}")
            
            usuario = next((u for u in self.usuarios if u.id == usuario_id), None)
            if usuario:
                logger.info(f"Usuário encontrado: {usuario_id} - {usuario.nome} (tipo: {usuario.tipo})")
                usuario_dict = usuario.to_dict()
                logger.info(f"Retornando dicionário do usuário: {usuario_dict}")
                return usuario_dict
            else:
                logger.warning(f"Usuário não encontrado: {usuario_id}")
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por ID {usuario_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def obter_usuario_por_email(self, email):
        """
        Obtém um usuário pelo email.
        
        Args:
            email (str): Email do usuário
            
        Returns:
            Usuario: O usuário encontrado ou None
        """
        try:
            usuario = next((u for u in self.usuarios if u.email == email), None)
            if usuario:
                logger.info(f"Usuário encontrado por email: {email}")
                return usuario.to_dict()
            else:
                logger.warning(f"Usuário não encontrado por email: {email}")
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por email {email}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    def obter_usuario_por_telefone(self, telefone):
        """
        Obtém um usuário pelo telefone.
        
        Args:
            telefone (str): Telefone do usuário
            
        Returns:
            Usuario: O usuário encontrado ou None
        """
        try:
            usuario = next((u for u in self.usuarios if u.telefone == telefone), None)
            if usuario:
                logger.info(f"Usuário encontrado por telefone: {telefone}")
                return usuario.to_dict()
            else:
                logger.warning(f"Usuário não encontrado por telefone: {telefone}")
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por telefone {telefone}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    def obter_usuario_por_credencial(self, credencial):
        """
        Obtém um usuário por email ou telefone.
        
        Args:
            credencial (str): Email ou telefone do usuário
            
        Returns:
            Usuario: O usuário encontrado ou None
        """
        try:
            # Verificar se é email
            if re.match(r"[^@]+@[^@]+\.[^@]+", credencial):
                return self.obter_usuario_por_email(credencial)
            # Caso contrário, considerar como telefone
            else:
                return self.obter_usuario_por_telefone(credencial)
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por credencial {credencial}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    def obter_usuario_por_token(self, token):
        """
        Obtém um usuário pelo token de redefinição de senha.
        
        Args:
            token (str): Token de redefinição
            
        Returns:
            Usuario: O usuário encontrado ou None
        """
        try:
            usuario = next((u for u in self.usuarios if u.reset_token == token), None)
            if usuario:
                logger.info(f"Usuário encontrado por token: {token}")
                return usuario.to_dict()
            else:
                logger.warning(f"Usuário não encontrado por token: {token}")
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por token: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    def autenticar_usuario(self, credencial, senha):
        """
        Autentica um usuário com email/telefone e senha.
        
        Args:
            credencial (str): Email ou telefone do usuário
            senha (str): Senha em texto puro
            
        Returns:
            Usuario: O usuário autenticado ou None
        """
        try:
            usuario = next((u for u in self.usuarios if (u.email == credencial or u.telefone == credencial)), None)
            if usuario and usuario.verificar_senha(senha):
                logger.info(f"Usuário {usuario.id} - {usuario.nome} autenticado com sucesso")
                return usuario.to_dict()
            logger.warning(f"Falha na autenticação para credencial: {credencial}")
            return None
        except Exception as e:
            logger.error(f"Erro ao autenticar usuário: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        
    def listar_usuarios(self, apenas_funcionarios=False):
        """
        Lista todos os usuários.
        
        Args:
            apenas_funcionarios (bool, optional): Se True, lista apenas funcionários. Padrão é False.
            
        Returns:
            list: Lista de usuários em formato dicionário
        """
        try:
            if not self.usuarios:
                logger.warning("Lista de usuários está vazia")
                return []
                
            if apenas_funcionarios:
                usuarios = [u.to_dict() for u in self.usuarios if u.tipo == "funcionario"]
            else:
                usuarios = [u.to_dict() for u in self.usuarios]
            logger.info(f"Listando {len(usuarios)} usuários")
            
            # Garantir que todos os usuários tenham suas informações completas
            for u in usuarios:
                # Garantir que todos os campos obrigatórios estejam presentes
                for campo in ['id', 'nome', 'email', 'telefone', 'tipo']:
                    if campo not in u:
                        logger.warning(f"Usuário sem campo obrigatório: {campo}")
                        if campo == 'tipo':
                            u[campo] = 'funcionario'  # valor padrão
                        else:
                            u[campo] = ""  # valor vazio para outros campos
            
            return usuarios
        except Exception as e:
            logger.error(f"Erro ao listar usuários: {str(e)}")
            logger.error(traceback.format_exc())
            return []
        
    def excluir_usuario(self, usuario_id):
        """
        Exclui um usuário.
        
        Args:
            usuario_id (str): ID do usuário
            
        Returns:
            bool: True se a exclusão foi bem-sucedida, False caso contrário
        """
        try:
            usuario = next((u for u in self.usuarios if u.id == usuario_id), None)
            if usuario:
                # Verificar se é o único gerente
                if usuario.tipo == "gerente" and len([u for u in self.usuarios if u.tipo == "gerente"]) <= 1:
                    raise ValueError("Não é possível excluir o único gerente do sistema")
                
                self.usuarios.remove(usuario)
                logger.info(f"Usuário excluído: {usuario_id}")
                return True
            logger.warning(f"Usuário não encontrado para exclusão: {usuario_id}")
            return False
        except Exception as e:
            logger.error(f"Erro ao excluir usuário {usuario_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

def main():
    """
    Função principal do programa
    """
    catalogo = Catalogo()
    
    # Exemplo de uso
    try:
        # Adicionar alguns produtos
        produto1 = catalogo.adicionar_produto(
            nome="Smartphone XYZ",
            descricao="Smartphone último modelo",
            preco=1999.99,
            quantidade_estoque=10,
            imagem_url="https://exemplo.com/smartphone.jpg"
        )
        
        produto2 = catalogo.adicionar_produto(
            nome="Notebook ABC",
            descricao="Notebook para trabalho",
            preco=3999.99,
            quantidade_estoque=5,
            imagem_url="https://exemplo.com/notebook.jpg"
        )

        # Listar produtos
        print("Produtos disponíveis:")
        for produto in catalogo.listar_produtos():
            print(f"- {produto['nome']}: R${produto['preco']:.2f}")

        # Criar um pedido
        pedido = catalogo.criar_pedido(
            produtos=[{'id': produto1['id'], 'quantidade': 1}, {'id': produto2['id'], 'quantidade': 1}],
            cliente_nome="João Silva",
            cliente_telefone="(11) 99999-9999",
            cliente_endereco="Rua Exemplo, 123"
        )
        
        print(f"\nPedido #{pedido['id']} criado com sucesso!")
        print(f"Status: {pedido['status']}")
        print(f"Cliente: {pedido['cliente_nome']}")

    except ValueError as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    main()