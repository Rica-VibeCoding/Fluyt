# 🚀 Fluyt Comercial API - Backend

API REST completa para gestão comercial de móveis planejados, construída com FastAPI, Supabase e arquitetura modular.

## 📋 Visão Geral

### Stack Tecnológica
- **FastAPI** 0.104+ - Framework web moderno e performático
- **Supabase** - Backend as a Service (PostgreSQL + Auth + Storage)
- **Pydantic** 2.0+ - Validação de dados type-safe
- **Python-JOSE** - Manipulação de tokens JWT
- **Pandas** - Processamento de XML e relatórios
- **Uvicorn** - Servidor ASGI de produção

### Arquitetura
```
backend/
├── core/                    # 🔧 Configurações centrais
│   ├── config.py           # Settings e variáveis de ambiente
│   ├── database.py         # Cliente Supabase + RLS
│   ├── auth.py             # JWT + middleware de autenticação
│   ├── exceptions.py       # Tratamento centralizado de erros
│   └── dependencies.py     # Dependency injection helpers
├── modules/                 # 📦 Módulos de negócio
│   ├── orcamentos/         # 💰 Core - Orçamentos
│   ├── clientes/           # 👥 Gestão de clientes
│   ├── ambientes/          # 🏠 Ambientes XML
│   ├── aprovacoes/         # ✅ Sistema de aprovação
│   ├── contratos/          # 📄 Geração de contratos
│   ├── configuracoes/      # ⚙️ Config por loja
│   └── ...                 # Outros módulos
└── main.py                 # 🎯 Aplicação principal
```

### Padrão de Módulo
Cada módulo segue a estrutura:
```
module_name/
├── controller.py           # 🛣️ Routes FastAPI
├── services.py            # 🔨 Lógica de negócio
├── repository.py          # 💾 Queries database
├── schemas.py             # 📝 Modelos Pydantic
└── tests/                 # 🧪 Testes unitários
```

## ⚡ Quick Start

### 1. Pré-requisitos
```bash
# Python 3.10+
python --version

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Instalação
```bash
# Instalar dependências
pip install -r requirements.txt

# Copiar arquivo de ambiente
cp env.example .env
```

### 3. Configuração (.env)
```env
# ===== SUPABASE =====
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# ===== JWT =====
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# ===== APLICAÇÃO =====
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# ===== CORS =====
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Executar
```bash
# Desenvolvimento (com reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ou diretamente
python main.py
```

### 5. Acessar
- **API Docs:** http://localhost:8000/api/v1/docs
- **Health Check:** http://localhost:8000/health
- **Root Info:** http://localhost:8000/

## 🔐 Autenticação e Segurança

### Sistema de Autenticação
- **JWT Bearer Token** obrigatório para todas as rotas protegidas
- **RLS (Row Level Security)** automático por `loja_id`
- **Middleware personalizado** para contexto de usuário

### Perfis de Usuário
```python
class PerfilUsuario(str, Enum):
    VENDEDOR = "VENDEDOR"        # Orçamentos próprios
    GERENTE = "GERENTE"          # Equipe da loja
    MEDIDOR = "MEDIDOR"          # Medições específicas
    ADMIN_MASTER = "ADMIN_MASTER" # Todas as lojas + configurações
```

### Dependências de Autorização
```python
# Exemplos de uso nos controllers
@router.get("/", dependencies=[Depends(get_current_user)])
@router.post("/", dependencies=[Depends(require_vendedor_ou_superior())])
@router.get("/admin", dependencies=[Depends(require_admin())])
```

## 🗃️ Banco de Dados

### Supabase + PostgreSQL
- **RLS habilitado** para isolamento por loja
- **Triggers automáticos** para numeração e auditoria
- **Schema versionado** conforme `docs/schema.md`

### Principais Tabelas
- `c_orcamentos` - Núcleo dos orçamentos
- `c_clientes` - Cadastro de clientes
- `c_ambientes` - Ambientes importados do XML
- `c_orcamento_custos_adicionais` - Custos específicos
- `config_loja` - Configurações por estabelecimento

### Operações com Database
```python
# Dependency injection automático
async def criar_orcamento(
    db: Client = Depends(get_database)  # RLS aplicado automaticamente
):
    # Operações isoladas por loja do usuário autenticado
    result = db.table('c_orcamentos').insert(data).execute()
```

## 📊 Funcionalidades Principais

### 💰 Sistema de Orçamentos
- Criação automática com todos os ambientes
- Cálculo de custos baseado em configurações
- Plano de pagamento flexível
- Sistema de aprovação hierárquica

### 🏠 Processamento XML
- Importação de XMLs do Promob
- Suporte a múltiplas coleções
- Extração automática de dados
- Validação e logs de processamento

### ✅ Aprovações
- Limites configuráveis por perfil
- Fluxo hierárquico (Vendedor → Gerente → Admin)
- Histórico completo de aprovações
- Notificações automáticas

### 📈 Relatórios
- **Admin Master:** Relatórios de margem detalhados
- **Gerente:** Métricas da equipe
- **Vendedor:** Métricas pessoais
- Export em Excel/PDF (futuro)

## 🔧 Configurações

### Variáveis de Ambiente
Todas as configurações são type-safe via Pydantic Settings:

```python
from core.config import settings

# Acesso às configurações
settings.supabase_url
settings.is_development
settings.cors_origins
settings.max_file_size_bytes
```

### Configurações por Loja
Cada loja pode ter:
- Limites de desconto personalizados
- Regras de comissão por faixa
- Custos operacionais específicos
- Numeração de orçamentos customizada

## 🚀 Deploy

### Desenvolvimento
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Produção
```bash
# Com Gunicorn + Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Ou Railway/Render deployment
# (configurações no Procfile/railway.toml)
```

### Variáveis de Produção
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
# JWT_SECRET_KEY deve ser criptograficamente segura
# CORS_ORIGINS deve ser restrito aos domínios específicos
```

## 🧪 Testes

### Estrutura de Testes
```bash
# Executar todos os testes
pytest

# Testes específicos
pytest modules/orcamentos/tests/

# Com coverage
pytest --cov=modules --cov-report=html
```

### Exemplo de Teste
```python
@pytest.mark.asyncio
async def test_criar_orcamento():
    # Setup de dados
    cliente_data = {...}
    
    # Teste da criação
    response = await client.post("/api/v1/orcamentos/", json=cliente_data)
    
    assert response.status_code == 201
    assert response.json()["numero"] is not None
```

## 📝 Logs e Monitoramento

### Logging Estruturado
```python
import logging
logger = logging.getLogger(__name__)

# Logs automáticos incluem:
logger.info("REQUEST: GET /api/v1/orcamentos/", extra={
    "user_id": user_id,
    "loja_id": loja_id,
    "request_id": request_id
})
```

### Headers de Debug
- `X-Request-ID` - ID único da requisição
- `X-Process-Time` - Tempo de processamento
- `X-Environment` - Ambiente atual (development)

## 🔄 Próximos Passos

### Task 1.14 ✅ Concluída
- [x] Setup FastAPI completo
- [x] Configuração de middlewares
- [x] Estrutura modular definida
- [x] Core components implementados

### Próximas Tasks
- **1.15** Implementar services e repositories
- **1.16** Conectar com Supabase real
- **1.17** Testes de integração
- **1.18** Deploy de desenvolvimento

## 🆘 Troubleshooting

### Erros Comuns

**ImportError: No module named 'core'**
```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Supabase connection failed**
```bash
# Verificar variáveis de ambiente
python -c "from core.config import settings; print(settings.supabase_url)"
```

**JWT decode error**
```bash
# Verificar JWT_SECRET_KEY
# Deve ser a mesma chave usada para gerar o token
```

### Logs Úteis
```bash
# Ver logs detalhados
uvicorn main:app --log-level debug

# Logs de SQL (Supabase)
export SUPABASE_LOG_LEVEL=DEBUG
```

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs detalhados
2. Consultar documentação do Supabase
3. Revisar configurações no arquivo `.env`
4. Checar permissões RLS no dashboard Supabase

**Status:** ✅ **PRONTO PARA DESENVOLVIMENTO**
