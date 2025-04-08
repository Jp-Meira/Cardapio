from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, flash
from flask_caching import Cache
from main import Catalogo, Produto, Pedido, Usuario
import json
from datetime import datetime, timedelta
import os
import logging
import traceback
import base64
from dotenv import load_dotenv
from utils import setup_logger, carregar_json_com_cache, salvar_json_com_cache, limpar_cache, hash_password, verify_password
import re

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging com rotação de arquivo
logger = setup_logger('app', 'app.log')

# Inicialização da aplicação Flask
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'vortex-catalogo-segredo-2025')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=int(os.getenv('SESSION_LIFETIME', '8')))

# Configuração de cache
cache = Cache(config={
    'CACHE_TYPE': os.getenv('CACHE_TYPE', 'SimpleCache'),
    'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
})
cache.init_app(app)

catalogo = Catalogo()

# Arquivos para armazenamento
PRODUTOS_FILE = 'produtos.json'
PEDIDOS_FILE = 'pedidos.json'
USUARIOS_FILE = 'usuarios.json'

def salvar_produtos():
    """Salva produtos em arquivo JSON com cache"""
    try:
        dados = {'produtos': [produto.to_dict() for produto in catalogo.produtos]}
        salvar_json_com_cache(PRODUTOS_FILE, dados)
        # Limpar cache da API para forçar atualização nas próximas requisições
        cache.delete('api_produtos')
        cache.delete_many('api_produto_*')
        logger.info("Produtos salvos com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar produtos: {e}")
        logger.error(traceback.format_exc())
        return False

def salvar_pedidos():
    """Salva pedidos em arquivo JSON com cache"""
    try:
        dados = {'pedidos': [pedido.to_dict() for pedido in catalogo.pedidos]}
        salvar_json_com_cache(PEDIDOS_FILE, dados)
        # Limpar cache da API para forçar atualização nas próximas requisições
        cache.delete('api_pedidos')
        cache.delete_many('api_pedido_*')
        logger.info("Pedidos salvos com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar pedidos: {e}")
        logger.error(traceback.format_exc())
        return False

def salvar_usuarios():
    """Salva usuários em arquivo JSON com cache"""
    try:
        dados = {'usuarios': [usuario.to_dict() for usuario in catalogo.usuarios]}
        salvar_json_com_cache(USUARIOS_FILE, dados)
        logger.info("Usuários salvos com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar usuários: {e}")
        logger.error(traceback.format_exc())
        return False

def carregar_produtos():
    """Carrega produtos do arquivo JSON com cache"""
    try:
        dados = carregar_json_com_cache(PRODUTOS_FILE)
        if dados and 'produtos' in dados:
            catalogo.produtos = []  # Limpa a lista atual
            for produto_data in dados.get('produtos', []):
                try:
                    produto = Produto.from_dict(produto_data)
                    catalogo.produtos.append(produto)
                except Exception as e:
                    logger.error(f"Erro ao carregar produto {produto_data.get('nome', 'desconhecido')}: {e}")
                    continue
            logger.info(f"Carregados {len(catalogo.produtos)} produtos")
            # Atualizar índices após carregar todos os produtos
            catalogo._atualizar_indices()
        else:
            logger.info("Arquivo produtos.json não encontrado ou vazio, usando produtos padrão")
            # Adicionar produtos padrão se não existirem
            if not catalogo.produtos:
                catalogo.adicionar_produto(
                    nome="Smartphone XYZ",
                    descricao="Smartphone último modelo",
                    preco=1999.99,
                    quantidade_estoque=10,
                    imagem_url="https://via.placeholder.com/300x200?text=Smartphone"
                )
                catalogo.adicionar_produto(
                    nome="Notebook ABC",
                    descricao="Notebook para trabalho",
                    preco=3999.99,
                    quantidade_estoque=5,
                    imagem_url="https://via.placeholder.com/300x200?text=Notebook"
                )
                catalogo.adicionar_produto(
                    nome="Tablet Pro",
                    descricao="Tablet profissional com tela retina",
                    preco=2499.99,
                    quantidade_estoque=18,
                    imagem_url="https://via.placeholder.com/300x200?text=Tablet"
                )
                # Índices já são atualizados ao adicionar produtos
                salvar_produtos()
        return True
    except Exception as e:
        logger.error(f"Erro ao carregar produtos: {e}")
        logger.error(traceback.format_exc())
        return False

def carregar_pedidos():
    """Carrega pedidos do arquivo JSON com cache"""
    try:
        dados = carregar_json_com_cache(PEDIDOS_FILE)
        if dados and 'pedidos' in dados:
            catalogo.pedidos = []  # Limpa a lista atual
            for pedido_data in dados.get('pedidos', []):
                pedido = Pedido.from_dict(pedido_data)
                # Corrigir status de pedidos existentes
                if pedido.status == 'Processado':
                    pedido.status = 'Concluído'
                catalogo.pedidos.append(pedido)
            logger.info(f"Carregados {len(catalogo.pedidos)} pedidos")
            # Atualizar índices após carregar todos os pedidos
            catalogo._atualizar_indices()
            # Salvar correções se houver
            salvar_pedidos()
        else:
            logger.info("Arquivo pedidos.json não encontrado ou vazio, criando novo")
            salvar_pedidos()
        return True
    except Exception as e:
        logger.error(f"Erro ao carregar pedidos: {e}")
        logger.error(traceback.format_exc())
        return False

def carregar_usuarios():
    """Carrega usuários do arquivo JSON com cache"""
    try:
        dados = carregar_json_com_cache(USUARIOS_FILE)
        if dados and 'usuarios' in dados:
            catalogo.usuarios = []  # Limpa a lista atual
            for usuario_data in dados.get('usuarios', []):
                try:
                    usuario = Usuario.from_dict(usuario_data)
                    catalogo.usuarios.append(usuario)
                except Exception as e:
                    logger.error(f"Erro ao carregar usuário {usuario_data.get('nome', 'desconhecido')}: {e}")
                    continue
            logger.info(f"Carregados {len(catalogo.usuarios)} usuários")
            # Atualizar índices após carregar todos os usuários
            catalogo._atualizar_indices()
        else:
            logger.info("Arquivo usuarios.json não encontrado ou vazio, criando usuário gerente padrão")
            # Criar o usuário gerente padrão
            if not catalogo.usuarios:
                catalogo.adicionar_usuario(
                    nome="Administrador",
                    email="admin@vortex.com",
                    telefone="11999999999",
                    senha="admin@2025", # Senha mais segura
                    tipo="gerente"
                )
                # Índices já são atualizados ao adicionar usuário
                salvar_usuarios()
        return True
    except Exception as e:
        logger.error(f"Erro ao carregar usuários: {e}")
        logger.error(traceback.format_exc())
        return False

# Carregar produtos, pedidos e usuários ao iniciar a aplicação
carregar_produtos()
carregar_pedidos()
carregar_usuarios()

# Garantir que o diretório static/images exista
def garantir_diretorio_imagens():
    """
    Cria o diretório static/images se não existir e adiciona uma imagem padrão.
    """
    try:
        if not os.path.exists('static/images'):
            os.makedirs('static/images', exist_ok=True)
            
        # Criar imagem padrão se não existir
        imagem_padrao = 'static/images/no-image.png'
        if not os.path.exists(imagem_padrao):
            # Criar uma imagem simples usando PIL se disponível
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Criar uma imagem 300x200 com fundo cinza
                img = Image.new('RGB', (300, 200), color = (240, 240, 240))
                d = ImageDraw.Draw(img)
                
                # Adicionar texto "Sem Imagem"
                try:
                    # Tentar usar uma fonte padrão
                    fnt = ImageFont.truetype("arial.ttf", 20)
                    d.text((100, 90), "Sem Imagem", font=fnt, fill=(80, 80, 80))
                except:
                    # Fallback para fonte padrão
                    d.text((100, 90), "Sem Imagem", fill=(80, 80, 80))
                    
                img.save(imagem_padrao)
                logger.info(f"Imagem padrão criada: {imagem_padrao}")
            except ImportError:
                # Se PIL não estiver disponível, criar arquivo vazio
                with open(imagem_padrao, 'wb') as f:
                    f.write(b'')
                logger.warning(f"PIL não encontrado. Criado arquivo vazio como imagem padrão: {imagem_padrao}")
    except Exception as e:
        logger.error(f"Erro ao criar imagem padrão: {e}")

# Garantir diretório static/images
garantir_diretorio_imagens()

# Funções auxiliares para manipulação de usuários
def _get_usuario_object(usuario_id):
    """Obtém um objeto Usuario pelo ID"""
    return next((u for u in catalogo.usuarios if u.id == usuario_id), None)

def _atualizar_senha_usuario(usuario_dict, nova_senha):
    """Atualiza a senha de um usuário a partir do dicionário"""
    usuario = _get_usuario_object(usuario_dict['id'])
    if usuario:
        usuario.atualizar_senha(nova_senha)
        return True
    return False

def _gerar_token_usuario(usuario_dict):
    """Gera um token de redefinição para um usuário a partir do dicionário"""
    usuario = _get_usuario_object(usuario_dict['id'])
    if usuario:
        return usuario.gerar_token_redefinicao()
    return None

@app.route('/static/images/<path:filename>')
def servir_imagem(filename):
    """
    Rota para servir imagens estáticas do diretório static/images.
    
    Args:
        filename (str): Nome do arquivo a ser servido
        
    Returns:
        Response: Arquivo solicitado
    """
    try:
        return send_from_directory('static/images', filename)
    except Exception as e:
        logger.error(f"Erro ao servir imagem {filename}: {str(e)}")
        logger.error(traceback.format_exc())
        return '', 404

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erro na página inicial: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('erro.html', mensagem="Erro ao carregar a página inicial")

@app.route('/pedidos')
def lista_pedidos():
    return render_template('pedidos.html')

@app.route('/estoque')
def estoque():
    try:
        logger.info("Acessando página de estoque")
        return render_template('estoque.html')
    except Exception as e:
        logger.error(f"Erro ao renderizar página de estoque: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('erro.html', mensagem="Erro ao carregar a página de estoque")

@app.route('/api/produtos')
@cache.cached(timeout=60, key_prefix='api_produtos')
def listar_produtos():
    try:
        # Recarregar produtos antes de listar para garantir dados atualizados
        logger.info("Requisição recebida para listar produtos")
        carregar_produtos()
        logger.info(f"Produtos carregados: {len(catalogo.produtos)} encontrados")
        
        produtos = catalogo.listar_produtos()
        logger.info(f"Retornando {len(produtos)} produtos em formato JSON")
        
        # Log dos primeiros 3 produtos para depuração
        if produtos and len(produtos) > 0:
            for i, produto in enumerate(produtos[:3]):
                logger.info(f"Produto {i+1}: ID={produto.get('id')} Nome={produto.get('nome')} Preço={produto.get('preco')}")
        
        return jsonify(produtos)
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"erro": "Erro ao processar a requisição"}), 500

@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos_api():
    try:
        carregar_pedidos()  # Recarrega os pedidos antes de listar
        pedidos = catalogo.listar_pedidos()
        
        # Não precisamos mais atualizar as informações dos produtos nos pedidos
        # pois agora armazenamos todas as informações relevantes no momento do pedido
        
        return jsonify(pedidos)
    except Exception as e:
        print(f"Erro ao listar pedidos: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/pedidos', methods=['POST'])
def criar_pedido_api():
    try:
        dados = request.get_json()
        
        # Validar estoque antes de criar o pedido
        for item in dados['produtos']:
            produto = next((p for p in catalogo.produtos if p.id == item['id']), None)
            if not produto:
                return jsonify({'erro': f'Produto com ID {item["id"]} não encontrado'}), 400
            if produto.quantidade_estoque < item['quantidade']:
                return jsonify({
                    'erro': f'Produto {produto.nome} não possui estoque suficiente. Disponível: {produto.quantidade_estoque}'
                }), 400
        
        # Criar o pedido
        pedido = catalogo.criar_pedido(
            produtos=dados['produtos'],
            cliente_nome=dados['cliente_nome'],
            cliente_telefone=dados['cliente_telefone'],
            cliente_endereco=dados['cliente_endereco']
        )
        
        # Salvar as alterações
        salvar_pedidos()
        salvar_produtos()
        
        # Obter o dicionário do pedido
        pedido_dict = pedido
        
        # Garantir que o status está presente (deve ser 'Pendente' por padrão)
        if isinstance(pedido_dict, dict) and 'status' not in pedido_dict:
            logger.warning("Pedido criado sem campo 'status', adicionando status 'Pendente'")
            pedido_dict['status'] = 'Pendente'
            
        return jsonify(pedido_dict)
    except ValueError as e:
        logger.error(f"Erro de validação ao criar pedido: {str(e)}")
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao criar pedido: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/pedidos/<pedido_id>/status', methods=['PUT'])
def atualizar_status_pedido(pedido_id):
    try:
        # Recarregar pedidos para garantir dados atualizados
        carregar_pedidos()
        
        # Encontrar o pedido pelo ID
        pedido = next((p for p in catalogo.pedidos if p.id == pedido_id), None)
        if not pedido:
            return jsonify({'erro': 'Pedido não encontrado'}), 404
            
        # Atualizar o status
        pedido.status = "Concluído"  # Mudar para Concluído
        
        # Salvar as alterações
        salvar_pedidos()
        
        return jsonify(pedido.to_dict())
    except Exception as e:
        print(f"Erro ao atualizar status do pedido: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/debug/pedidos')
def debug_pedidos():
    try:
        print("Verificando arquivo pedidos.json...")
        with open(PEDIDOS_FILE, 'r', encoding='utf-8') as arquivo:
            conteudo = json.load(arquivo)
            print(f"Conteúdo do arquivo: {conteudo}")
            return jsonify({
                'arquivo_existe': True,
                'conteudo': conteudo,
                'pedidos_memoria': len(catalogo.pedidos),
                'erro': None
            })
    except FileNotFoundError:
        print("Arquivo pedidos.json não encontrado")
        return jsonify({
            'arquivo_existe': False,
            'mensagem': 'Arquivo pedidos.json não encontrado',
            'erro': None
        })
    except Exception as e:
        print(f"Erro ao ler arquivo pedidos.json: {str(e)}")
        return jsonify({
            'arquivo_existe': True,
            'erro': str(e)
        })

@app.route('/api/produtos/<produto_id>', methods=['PUT'])
def atualizar_produto_api(produto_id):
    try:
        logger.info(f"Tentando atualizar produto ID: {produto_id}")
        dados = request.json
        
        if not dados:
            logger.error("Dados do produto não fornecidos")
            return jsonify({'erro': 'Dados do produto não fornecidos'}), 400
            
        # Encontrar o produto a ser atualizado
        produto = None
        for p in catalogo.produtos:
            if p.id == produto_id:
                produto = p
                break
                
        if not produto:
            logger.error(f"Produto com ID {produto_id} não encontrado")
            return jsonify({'erro': 'Produto não encontrado'}), 404
            
        # Atualizar os dados do produto
        if 'nome' in dados:
            produto.nome = dados['nome']
        if 'descricao' in dados:
            produto.descricao = dados['descricao']
        if 'preco' in dados:
            produto.preco = float(dados['preco'])
        if 'quantidade_estoque' in dados:
            produto.quantidade_estoque = int(dados['quantidade_estoque'])
        if 'imagem_url' in dados:
            produto.imagem_url = dados['imagem_url']
            
        # Atualizar a data de atualização
        produto.data_atualizacao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
        # Salvar as alterações
        salvar_produtos()
        
        logger.info(f"Produto {produto_id} atualizado com sucesso")
        return jsonify(produto.to_dict())
    except Exception as e:
        logger.error(f"Erro ao atualizar produto: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos/<produto_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix=lambda: f'api_produto_{request.view_args["produto_id"]}')
def obter_produto(produto_id):
    try:
        logger.info(f"Requisição para obter produto {produto_id}")
        produto = catalogo.buscar_produto(produto_id)
        if produto:
            logger.info(f"Produto encontrado: {produto_id}")
            return jsonify(produto.to_dict())
        else:
            logger.warning(f"Produto não encontrado: {produto_id}")
            return jsonify({"erro": "Produto não encontrado"}), 404
    except Exception as e:
        logger.error(f"Erro ao obter produto {produto_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"erro": "Erro ao processar a requisição"}), 500

@app.route('/api/produtos/<produto_id>', methods=['DELETE'])
def excluir_produto_api(produto_id):
    try:
        logger.info(f"Tentando excluir produto ID: {produto_id}")
        
        # Encontrar o produto a ser excluído
        produto = None
        index_to_remove = -1
        for i, p in enumerate(catalogo.produtos):
            if p.id == produto_id:
                produto = p
                index_to_remove = i
                break
                
        if not produto:
            logger.error(f"Produto com ID {produto_id} não encontrado")
            return jsonify({'erro': 'Produto não encontrado'}), 404
            
        # Verificar se o produto está em algum pedido pendente
        for pedido in catalogo.pedidos:
            if pedido.status == 'Pendente':
                for item in pedido.produtos:
                    if item['id'] == produto_id:
                        logger.error(f"Produto {produto_id} está em pedidos pendentes e não pode ser excluído")
                        return jsonify({'erro': 'Este produto está em pedidos pendentes e não pode ser excluído'}), 400
        
        # Remover o produto
        if index_to_remove >= 0:
            del catalogo.produtos[index_to_remove]
            
        # Salvar as alterações
        salvar_produtos()
        
        logger.info(f"Produto {produto_id} excluído com sucesso")
        return jsonify({'mensagem': 'Produto excluído com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao excluir produto: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos', methods=['POST'])
def criar_produto_api():
    try:
        logger.info("Tentando criar novo produto")
        dados = request.json
        
        if not dados:
            logger.error("Dados do produto não fornecidos")
            return jsonify({'erro': 'Dados do produto não fornecidos'}), 400
            
        # Validar dados obrigatórios
        campos_obrigatorios = ['nome', 'descricao', 'preco']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                logger.error(f"Campo obrigatório '{campo}' não fornecido")
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
                
        # Criar o produto
        novo_produto = Produto(
            nome=dados['nome'],
            descricao=dados['descricao'],
            preco=float(dados['preco']),
            quantidade_estoque=int(dados.get('quantidade_estoque', 0)),
            imagem_url=dados.get('imagem_url')
        )
        
        catalogo.produtos.append(novo_produto)
        
        # Salvar as alterações
        salvar_produtos()
        
        logger.info(f"Novo produto criado com ID: {novo_produto.id}")
        return jsonify(novo_produto.to_dict()), 201
    except Exception as e:
        logger.error(f"Erro ao criar produto: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/pedidos/<pedido_id>', methods=['DELETE'])
def excluir_pedido_api(pedido_id):
    try:
        logger.info(f"Tentando excluir pedido ID: {pedido_id}")
        
        # Encontrar o pedido pelo ID
        carregar_pedidos()  # Garantir dados atualizados
        
        index_to_remove = -1
        pedido = None
        for i, p in enumerate(catalogo.pedidos):
            if p.id == pedido_id:
                pedido = p
                index_to_remove = i
                break
                
        if not pedido:
            logger.error(f"Pedido com ID {pedido_id} não encontrado")
            return jsonify({'erro': 'Pedido não encontrado'}), 404
            
        # Verificar se o pedido está pendente (não permitir excluir pedidos pendentes)
        if pedido.status == 'Pendente':
            logger.error(f"Tentativa de excluir pedido pendente {pedido_id}")
            return jsonify({'erro': 'Pedidos pendentes não podem ser excluídos. Conclua o pedido antes de excluí-lo.'}), 400
            
        # Remover o pedido
        if index_to_remove >= 0:
            del catalogo.pedidos[index_to_remove]
            
        # Salvar as alterações
        salvar_pedidos()
        
        logger.info(f"Pedido {pedido_id} excluído com sucesso")
        return jsonify({'mensagem': 'Pedido excluído com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao excluir pedido: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

# Verificação de login
def login_required(f):
    """
    Decorador para verificar se o usuário está logado.
    Redireciona para a página de login se não estiver.
    """
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login', proximo=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Verificação de gerente
def gerente_required(f):
    """
    Decorador para verificar se o usuário é gerente ou desenvolvedor.
    Redireciona para a página principal se não for.
    """
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            logger.warning("gerente_required: usuário não está na sessão")
            return redirect(url_for('login', proximo=request.url))
        
        logger.info(f"gerente_required: verificando permissões para usuário ID: {session['usuario_id']}, tipo: {session.get('usuario_tipo', 'não definido')}")
        
        usuario = catalogo.obter_usuario_por_id(session['usuario_id'])
        if not usuario:
            logger.error(f"gerente_required: usuário ID {session['usuario_id']} não encontrado")
            flash('Erro ao verificar usuário', 'danger')
            return redirect(url_for('index'))
        
        logger.info(f"gerente_required: usuário encontrado - {usuario.get('nome', 'N/A')}, tipo: {usuario.get('tipo', 'N/A')}")
        
        if usuario['tipo'] != "gerente" and usuario['tipo'] != "dev":
            logger.warning(f"gerente_required: acesso negado para usuário {usuario.get('nome', 'N/A')} (tipo: {usuario.get('tipo', 'N/A')})")
            flash('Acesso restrito a gerentes e desenvolvedores', 'danger')
            return redirect(url_for('index'))
        
        logger.info(f"gerente_required: acesso concedido para usuário {usuario.get('nome', 'N/A')} (tipo: {usuario.get('tipo', 'N/A')})")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se já estiver logado, redirecionar para a página inicial
    if 'usuario_id' in session:
        return redirect(url_for('index'))
    
    proximo = request.args.get('proximo', url_for('index'))
    
    if request.method == 'POST':
        credencial = request.form.get('credencial')
        senha = request.form.get('senha')
        
        if not credencial or not senha:
            flash('Por favor, informe suas credenciais', 'warning')
            return render_template('login.html', proximo=proximo)
        
        usuario = catalogo.autenticar_usuario(credencial, senha)
        
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_tipo'] = usuario['tipo']
            session.permanent = True
            
            logger.info(f"Login bem-sucedido: {usuario['nome']} ({usuario['tipo']})")
            
            # Redirecionar para a página solicitada anteriormente ou a página inicial
            return redirect(proximo)
        else:
            flash('Credenciais inválidas', 'danger')
            logger.warning(f"Tentativa de login falhou para credencial: {credencial}")
    
    return render_template('login.html', proximo=proximo)

@app.route('/logout')
def logout():
    # Remover informações de sessão
    session.pop('usuario_id', None)
    session.pop('usuario_nome', None)
    session.pop('usuario_tipo', None)
    session.clear()
    
    flash('Você saiu do sistema', 'info')
    return redirect(url_for('login'))

@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        credencial = request.form.get('credencial')
        
        if not credencial:
            flash('Por favor, informe seu email ou telefone', 'warning')
            return render_template('esqueci_senha.html')
        
        usuario = catalogo.obter_usuario_por_credencial(credencial)
        
        if usuario:
            # Impedir a recuperação de senha para desenvolvedores
            if usuario['tipo'] == 'dev':
                logger.warning(f"Tentativa de recuperação de senha para usuário desenvolvedor: {usuario['id']} - {usuario['nome']}")
                flash('Não é possível redefinir a senha para este tipo de conta. Entre em contato com o suporte.', 'warning')
                return render_template('esqueci_senha.html')
            
            # Gerar token para redefinição de senha
            token = _gerar_token_usuario(usuario)
            
            # Aqui seria implementado o envio do email/SMS com o link de redefinição
            # Para fins de demonstração, apenas exibiremos o link na tela
            
            # Salvar as alterações
            salvar_usuarios()
            
            flash('Um link para redefinição de senha foi enviado. Por favor, verifique seu email ou telefone.', 'success')
            flash(f'Link de redefinição (demonstração): /redefinir-senha/{token}', 'info')
            logger.info(f"Token de redefinição gerado para usuário: {usuario['id']} - {usuario['nome']}")
            
            return redirect(url_for('login'))
        else:
            flash('Email ou telefone não encontrado', 'danger')
            logger.warning(f"Tentativa de recuperação de senha falhou para credencial: {credencial}")
    
    return render_template('esqueci_senha.html')

@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    # Verificar se o token é válido
    usuario = catalogo.obter_usuario_por_token(token)
    
    if not usuario:
        flash('Link de redefinição inválido ou expirado', 'danger')
        return redirect(url_for('login'))
    
    # Impedir redefinição de senha para desenvolvedores
    if usuario['tipo'] == 'dev':
        flash('Não é permitido redefinir a senha de desenvolvedores através deste método', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if not senha or not confirmar_senha:
            flash('Por favor, preencha todos os campos', 'warning')
            return render_template('redefinir_senha.html', token=token)
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem', 'warning')
            return render_template('redefinir_senha.html', token=token)
        
        # Atualizar a senha
        if _atualizar_senha_usuario(usuario, senha):
            # Salvar as alterações
            salvar_usuarios()
        
            flash('Senha redefinida com sucesso. Você já pode fazer login com sua nova senha.', 'success')
            logger.info(f"Senha redefinida para usuário: {usuario['id']} - {usuario['nome']}")
        
            return redirect(url_for('login'))
        else:
            flash('Erro ao redefinir senha. Tente novamente.', 'danger')
    
    return render_template('redefinir_senha.html', token=token)

@app.route('/usuarios')
@gerente_required
def listar_usuarios():
    return render_template('usuarios.html')

@app.route('/api/usuarios', methods=['GET'])
@gerente_required
def listar_usuarios_api():
    try:
        logger.info("Recebida solicitação para listar usuários")
        usuarios = catalogo.listar_usuarios()
        
        if not usuarios:
            logger.warning("Nenhum usuário encontrado na chamada listar_usuarios")
            return jsonify([])
        
        # Remover informações sensíveis
        for usuario in usuarios:
            usuario.pop('senha_hash', None)
            usuario.pop('reset_token', None)
        
        logger.info(f"Retornando {len(usuarios)} usuários")
        return jsonify(usuarios)
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/usuarios', methods=['POST'])
@gerente_required
def criar_usuario_api():
    try:
        dados = request.json
        
        if not dados:
            return jsonify({'erro': 'Dados do usuário não fornecidos'}), 400
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome', 'email', 'telefone', 'senha', 'tipo']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        # Validar formato dos dados
        # Validar nome (mínimo duas palavras)
        nome = dados['nome'].strip()
        palavras_nome = nome.split()
        if len(palavras_nome) < 2:
            return jsonify({'erro': 'O nome deve conter pelo menos nome e sobrenome'}), 400
        
        # Validar comprimento do nome
        if len(nome) < 5 or len(nome) > 100:
            return jsonify({'erro': 'Nome deve ter entre 5 e 100 caracteres'}), 400
            
        # Verificar se o nome contém apenas letras e espaços
        if not all(c.isalpha() or c.isspace() for c in nome):
            return jsonify({'erro': 'Nome deve conter apenas letras e espaços'}), 400
            
        # Validar email
        email = dados['email'].strip()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return jsonify({'erro': 'Formato de email inválido'}), 400
            
        # Validar tamanho do email
        if len(email) > 150:
            return jsonify({'erro': 'Email muito longo (máximo 150 caracteres)'}), 400
            
        # Validar telefone (pelo menos 10 dígitos)
        telefone = dados['telefone'].strip()
        telefone_digits = re.sub(r'\D', '', telefone)
        if len(telefone_digits) < 10 or len(telefone_digits) > 11:
            return jsonify({'erro': 'Telefone deve ter entre 10 e 11 dígitos'}), 400
        
        # Validar formato do telefone
        if not re.match(r"^\(?(\d{2})\)?[-. ]?(\d{4,5})[-. ]?(\d{4})$", telefone):
            return jsonify({'erro': 'Formato de telefone inválido. Use (XX) XXXXX-XXXX ou (XX) XXXX-XXXX'}), 400
            
        # Validar senha (mínimo 6 caracteres)
        senha = dados['senha']
        if len(senha) < 6:
            return jsonify({'erro': 'A senha deve ter pelo menos 6 caracteres'}), 400
        
        # Verificar se a senha tem pelo menos um número e uma letra
        if not (any(c.isalpha() for c in senha) and any(c.isdigit() for c in senha)):
            return jsonify({'erro': 'A senha deve conter pelo menos uma letra e um número'}), 400
            
        # Validar tipo de usuário
        tipo = dados['tipo']
        if tipo not in ['funcionario', 'gerente', 'dev']:
            return jsonify({'erro': 'Tipo de usuário inválido. Use "funcionario", "gerente" ou "dev"'}), 400
        
        # Apenas desenvolvedores podem criar outros desenvolvedores
        if tipo == 'dev' and session['usuario_tipo'] != 'dev':
            return jsonify({'erro': 'Apenas desenvolvedores podem criar outros desenvolvedores'}), 403
        
        # Criar usuário
        try:
            usuario = catalogo.adicionar_usuario(
                nome=nome,
                email=email,
                telefone=telefone,
                senha=senha,
                tipo=tipo
            )
            
            # Salvar as alterações
            salvar_usuarios()
            
            # Remover informações sensíveis
            usuario_dict = usuario
            usuario_dict.pop('senha_hash', None)
            usuario_dict.pop('reset_token', None)
            
            return jsonify(usuario_dict), 201
        except ValueError as e:
            return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/usuarios/<usuario_id>', methods=['DELETE'])
@gerente_required
def excluir_usuario_api(usuario_id):
    try:
        # Não permitir exclusão do desenvolvedor/administrador
        if usuario_id == "1":
            return jsonify({'erro': 'O desenvolvedor não pode ser excluído'}), 403
            
        # Verificar se não está tentando excluir a si mesmo
        if session.get('usuario_id') == usuario_id:
            return jsonify({'erro': 'Não é possível excluir seu próprio usuário'}), 400
        
        if catalogo.excluir_usuario(usuario_id):
            # Salvar as alterações
            salvar_usuarios()
            
            return jsonify({'mensagem': 'Usuário excluído com sucesso'})
        else:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao excluir usuário: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/produtos/<produto_id>/estoque', methods=['PUT'])
def atualizar_estoque_api(produto_id):
    try:
        dados = request.json
        logger.info(f"Tentando atualizar estoque do produto ID: {produto_id}")
        
        if not dados or 'quantidade' not in dados:
            logger.error("Quantidade não fornecida para atualização de estoque")
            return jsonify({'erro': 'É necessário fornecer a quantidade a ser adicionada'}), 400
            
        # Encontrar o produto
        produto = None
        for p in catalogo.produtos:
            if p.id == produto_id:
                produto = p
                break
                
        if not produto:
            logger.error(f"Produto com ID {produto_id} não encontrado")
            return jsonify({'erro': 'Produto não encontrado'}), 404
            
        # Converter para inteiro
        try:
            quantidade = int(dados['quantidade'])
        except (ValueError, TypeError):
            logger.error(f"Quantidade inválida: {dados['quantidade']}")
            return jsonify({'erro': 'Quantidade deve ser um número inteiro'}), 400
            
        # Atualizar o estoque
        try:
            produto.atualizar_estoque(quantidade)
            # Salvar as alterações
            salvar_produtos()
            
            logger.info(f"Estoque do produto {produto_id} atualizado com sucesso. Nova quantidade: {produto.quantidade_estoque}")
            return jsonify({
                'mensagem': 'Estoque atualizado com sucesso',
                'produto_id': produto_id,
                'nova_quantidade': produto.quantidade_estoque
            })
        except ValueError as e:
            logger.error(f"Erro ao atualizar estoque: {str(e)}")
            return jsonify({'erro': str(e)}), 400
            
    except Exception as e:
        logger.error(f"Erro ao atualizar estoque do produto: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@app.route('/api/usuarios/verificar-senha', methods=['POST'])
@gerente_required
def verificar_senha_gerente():
    try:
        dados = request.json
        senha = dados.get('senha')
        
        if not senha:
            return jsonify({'erro': 'Senha não fornecida'}), 400
        
        # Verificar a senha do gerente logado
        usuario_obj = _get_usuario_object(session['usuario_id'])
        if usuario_obj and usuario_obj.verificar_senha(senha):
            return jsonify({'sucesso': True}), 200
        else:
            return jsonify({'erro': 'Senha incorreta'}), 401
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/api/usuarios/<usuario_id>/senha', methods=['GET'])
@gerente_required
def obter_senha_usuario(usuario_id):
    try:
        usuario = catalogo.obter_usuario_por_id(usuario_id)
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        # Aqui nós retornamos uma senha fictícia mas segura para fins de demonstração
        # Em um ambiente de produção, seria mais seguro não armazenar ou retornar senhas em texto claro
        senha_ficticia = f"senha-usuario-{usuario_id}"
        
        return jsonify({'senha': senha_ficticia}), 200
    except Exception as e:
        logger.error(f"Erro ao obter senha: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/api/usuarios/<usuario_id>', methods=['PUT'])
@gerente_required
def atualizar_usuario_api(usuario_id):
    try:
        # Não permitir edição do desenvolvedor/administrador
        if usuario_id == "1":
            return jsonify({'erro': 'O desenvolvedor não pode ser editado'}), 403
            
        dados = request.json
        
        if not dados:
            return jsonify({'erro': 'Dados do usuário não fornecidos'}), 400
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['nome', 'email', 'telefone', 'tipo']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        # Obter o usuário atual para verificar se já é um desenvolvedor
        usuario_atual = catalogo.obter_usuario_por_id(usuario_id)
        if not usuario_atual:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        # Impedir que qualquer usuário altere o tipo de um desenvolvedor
        if usuario_atual['tipo'] == 'dev' and dados['tipo'] != 'dev':
            return jsonify({'erro': 'Não é permitido alterar o tipo de um desenvolvedor'}), 403
            
        # Apenas desenvolvedores podem alterar um usuário para desenvolvedor
        if dados['tipo'] == 'dev' and session['usuario_tipo'] != 'dev':
            return jsonify({'erro': 'Apenas desenvolvedores podem alterar um usuário para desenvolvedor'}), 403
        
        # Validar formato dos dados
        # Validar nome (mínimo duas palavras)
        nome = dados['nome'].strip()
        palavras_nome = nome.split()
        if len(palavras_nome) < 2:
            return jsonify({'erro': 'O nome deve conter pelo menos nome e sobrenome'}), 400
        
        # Validar comprimento do nome
        if len(nome) < 5 or len(nome) > 100:
            return jsonify({'erro': 'Nome deve ter entre 5 e 100 caracteres'}), 400
            
        # Verificar se o nome contém apenas letras e espaços
        if not all(c.isalpha() or c.isspace() for c in nome):
            return jsonify({'erro': 'Nome deve conter apenas letras e espaços'}), 400
            
        # Validar email
        email = dados['email'].strip()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return jsonify({'erro': 'Formato de email inválido'}), 400
            
        # Validar tamanho do email
        if len(email) > 150:
            return jsonify({'erro': 'Email muito longo (máximo 150 caracteres)'}), 400
            
        # Validar telefone (pelo menos 10 dígitos)
        telefone = dados['telefone'].strip()
        telefone_digits = re.sub(r'\D', '', telefone)
        if len(telefone_digits) < 10 or len(telefone_digits) > 11:
            return jsonify({'erro': 'Telefone deve ter entre 10 e 11 dígitos'}), 400
        
        # Validar formato do telefone
        if not re.match(r"^\(?(\d{2})\)?[-. ]?(\d{4,5})[-. ]?(\d{4})$", telefone):
            return jsonify({'erro': 'Formato de telefone inválido. Use (XX) XXXXX-XXXX ou (XX) XXXX-XXXX'}), 400
            
        # Validar tipo de usuário
        tipo = dados['tipo']
        if tipo not in ['funcionario', 'gerente', 'dev']:
            return jsonify({'erro': 'Tipo de usuário inválido. Use "funcionario", "gerente" ou "dev"'}), 400
            
        # Validar senha se fornecida
        if 'senha' in dados and dados['senha']:
            senha = dados['senha']
            if len(senha) < 6:
                return jsonify({'erro': 'A senha deve ter pelo menos 6 caracteres'}), 400
            
            # Verificar se a senha tem pelo menos um número e uma letra
            if not (any(c.isalpha() for c in senha) and any(c.isdigit() for c in senha)):
                return jsonify({'erro': 'A senha deve conter pelo menos uma letra e um número'}), 400
                
        # Verificar se email já está em uso por outro usuário
        for u in catalogo.usuarios:
            if u.id != usuario_id and u.email == email:
                return jsonify({'erro': 'Email já cadastrado para outro usuário'}), 400
                
        # Verificar se telefone já está em uso por outro usuário
        for u in catalogo.usuarios:
            if u.id != usuario_id and u.telefone == telefone:
                return jsonify({'erro': 'Telefone já cadastrado para outro usuário'}), 400
        
        # Atualizar dados do usuário
        for u in catalogo.usuarios:
            if u.id == usuario_id:
                u.nome = nome
                u.email = email
                u.telefone = telefone
                u.tipo = tipo
        
        # Atualizar senha apenas se fornecida
        if 'senha' in dados and dados['senha']:
            u.senha_hash = hash_password(dados['senha'])
        
        # Salvar alterações
        salvar_usuarios()
        
        # Retornar versão sem dados sensíveis
        usuario_dict = u.to_dict()
        usuario_dict.pop('senha_hash', None)
        usuario_dict.pop('reset_token', None)
        
        return jsonify(usuario_dict), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

if __name__ == "__main__":
    # Imprimir banner
    print("\n" + "="*60)
    print(" Sistema de Catálogo e Gestão de Pedidos - Vortex ".center(60, "="))
    print("="*60)
    print("\nIniciando servidor...")
    print("Para uma experiência melhor, use o script run.py para iniciar o aplicativo.")
    
    # Iniciar servidor
    logger.info("============================================================")
    logger.info("Iniciando servidor de catálogo e pedidos")
    logger.info("Acesse a aplicação em: http://localhost:5000")
    logger.info("============================================================")
    
    # Definir host e porta
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Iniciar o servidor
    app.run(host=host, port=port, debug=debug) 