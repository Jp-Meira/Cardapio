# Sistema de Catálogo e Gestão de Pedidos

Sistema completo para gerenciamento de catálogo de produtos, estoque e pedidos com interface web responsiva.

## Características

- **Catálogo de Produtos**: Visualização, adição, edição e remoção de produtos
- **Gestão de Estoque**: Controle de quantidade de produtos em tempo real
- **Processamento de Pedidos**: Criação e acompanhamento de pedidos
- **Interface Responsiva**: Layout adaptável para dispositivos móveis e desktop
- **Logs Detalhados**: Sistema com logs completos para facilitar manutenção
- **Cache Inteligente**: Sistema de cache para melhorar performance
- **Segurança Aprimorada**: Senhas armazenadas com bcrypt e configurações via variáveis de ambiente

## Requisitos

- Python 3.7+
- Flask 2.3+
- Bibliotecas listadas em requirements.txt
- Navegador web moderno

## Instalação

1. Clone o repositório:
```
git clone [URL do repositório]
cd catalogo
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure o arquivo .env (opcional):
```
# Exemplo de .env
FLASK_SECRET_KEY=sua_chave_secreta_aqui
FLASK_ENV=development
FLASK_DEBUG=1
CACHE_TYPE=SimpleCache
CACHE_DEFAULT_TIMEOUT=300
SESSION_LIFETIME=8
```

## Atualização (se vindo de versão anterior)

Se você está atualizando de uma versão anterior, execute o script de migração de senhas:
```
python migrar_senhas.py
```
Este script converterá as senhas antigas para o novo formato bcrypt mais seguro.

## Execução

Para iniciar o servidor:
```
python app.py
```

Após iniciar, acesse a aplicação em:
```
http://localhost:5000
```

## Estrutura do Projeto

```
catalogo/
├── app.py              # Aplicação principal Flask
├── main.py             # Classes e lógica de negócio
├── utils.py            # Funções utilitárias e otimizações
├── .env                # Configurações de ambiente
├── produtos.json       # Banco de dados de produtos
├── pedidos.json        # Banco de dados de pedidos
├── usuarios.json       # Banco de dados de usuários
├── app.log             # Arquivo de logs (com rotação)
├── requirements.txt    # Dependências do projeto
├── migrar_senhas.py    # Script de migração de senhas
├── static/             # Arquivos estáticos
│   └── images/         # Imagens de produtos
└── templates/          # Templates HTML
    ├── index.html      # Página principal/catálogo
    ├── pedidos.html    # Gerenciamento de pedidos
    ├── estoque.html    # Gerenciamento de estoque
    ├── usuarios.html   # Gerenciamento de usuários
    ├── login.html      # Página de login
    ├── nav.html        # Barra de navegação
    ├── erro.html       # Página de erro genérica
    └── 404.html        # Página de erro 404
```

## Funcionalidades

### Catálogo de Produtos
- Visualização em grade com imagens e informações básicas
- Detalhes do produto com descrição completa
- Carrinho de compras com persistência local
- Filtros e ordenação

### Gerenciamento de Estoque
- Adição de novos produtos
- Edição de informações (nome, descrição, preço, etc.)
- Controle de quantidade em estoque
- Remoção de produtos (bloqueada se estiver em pedido pendente)

### Processamento de Pedidos
- Criação de novos pedidos com validação de estoque
- Atualização de status (Pendente -> Concluído)
- Filtros por diversos critérios (data, cliente, status)
- Exclusão de pedidos concluídos

### Segurança
- Senhas armazenadas usando hash bcrypt
- Sessões com tempo de expiração configurável
- Chaves secretas armazenadas em variáveis de ambiente
- Validação de dados de entrada

## Otimizações Implementadas

### Performance
- Sistema de cache para API e carregamento de dados
- Índices para busca rápida de produtos, pedidos e usuários
- Rotação de logs para evitar arquivos muito grandes

### Segurança
- Uso de bcrypt para hash de senhas
- Variáveis de ambiente para informações sensíveis
- Validação de dados melhorada

### Manutenibilidade
- Código refatorado e organizado em módulos
- Logs detalhados com rotação de arquivos
- Funções reutilizáveis para operações comuns
- Cache de arquivos JSON para reduzir I/O

## API REST

O sistema disponibiliza uma API REST para integração com outros sistemas:

### Produtos
- `GET /api/produtos` - Listar todos os produtos
- `GET /api/produtos/{id}` - Obter produto específico
- `POST /api/produtos` - Criar novo produto
- `PUT /api/produtos/{id}` - Atualizar produto existente
- `DELETE /api/produtos/{id}` - Remover produto

### Pedidos
- `GET /api/pedidos` - Listar todos os pedidos
- `GET /api/pedidos/{id}` - Obter pedido específico
- `POST /api/pedidos` - Criar novo pedido
- `PUT /api/pedidos/{id}/status` - Atualizar status do pedido
- `DELETE /api/pedidos/{id}` - Remover pedido concluído

## Logs e Depuração

O sistema mantém logs detalhados em `app.log` com os seguintes níveis:
- INFO: Operações normais e informações
- WARNING: Situações inesperadas mas não críticas
- ERROR: Problemas que exigem atenção

O sistema implementa rotação de logs para evitar arquivos muito grandes.

## Contribuição

Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit de suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Envie para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request