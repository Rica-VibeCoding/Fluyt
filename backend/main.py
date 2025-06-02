"""
Aplicação principal do Fluyt Comercial - FastAPI.
Configura middleware, routers, documentação e segurança.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid

# Core imports
from core.config import get_settings
from core.auth import AuthMiddleware
from core.exceptions import register_exception_handlers

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Configura recursos na inicialização e limpa na finalização.
    """
    # Startup
    logger.info("🚀 Iniciando Fluyt Comercial API...")
    settings = get_settings()
    
    # Validação de configurações críticas na inicialização
    try:
        if not settings.supabase_url:
            raise ValueError("SUPABASE_URL não configurada")
        if not settings.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY não configurada")
        
        logger.info(f"✅ Configurações validadas - Ambiente: {settings.environment}")
        logger.info(f"📊 Supabase URL: {settings.supabase_url}")
        logger.info(f"🔐 JWT configurado - Expiração: {settings.jwt_access_token_expire_minutes}min")
        
    except Exception as e:
        logger.error(f"❌ Erro na validação de configurações: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Finalizando Fluyt Comercial API...")


# Configuração da aplicação FastAPI
settings = get_settings()

app = FastAPI(
    title="Fluyt Comercial API",
    description="""
    ## 🏢 Sistema de Gestão Comercial para Móveis Planejados
    
    API REST completa para gerenciamento de orçamentos, clientes, ambientes e contratos.
    
    ### ✨ Principais Funcionalidades:
    
    - **👥 Gestão de Clientes:** CRUD completo com validações
    - **🏠 Ambientes:** Importação e processamento de XML do Promob
    - **💰 Orçamentos:** Criação automática com cálculo de custos e margens
    - **✅ Aprovações:** Sistema hierárquico baseado em limites de desconto
    - **📄 Contratos:** Geração automática a partir de orçamentos
    - **⚙️ Configurações:** Regras de negócio configuráveis por loja
    - **📊 Relatórios:** Dashboards e relatórios de margem (por perfil)
    
    ### 🔐 Autenticação:
    - JWT Bearer Token obrigatório
    - RLS (Row Level Security) automático por loja
    - Controle de acesso por perfil (Vendedor, Gerente, Admin Master)
    
    ### 🏪 Multi-loja:
    - Isolamento completo de dados por loja
    - Admin Master visualiza todas as lojas
    - Configurações independentes por estabelecimento
    """,
    version=settings.api_version,
    openapi_url=f"/api/{settings.api_version}/openapi.json" if not settings.is_production else None,
    docs_url=f"/api/{settings.api_version}/docs" if not settings.is_production else None,
    redoc_url=f"/api/{settings.api_version}/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# ===== MIDDLEWARES =====

# 1. Request ID para rastreamento
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Adiciona ID único para cada requisição para rastreamento de logs"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Adiciona no header de resposta
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 2. Logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log detalhado de todas as requisições"""
    start_time = time.time()
    
    # Log da requisição
    logger.info(
        f"🔵 REQUEST: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "request_id": getattr(request.state, 'request_id', None),
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": request.client.host if request.client else ""
        }
    )
    
    # Processa requisição
    response = await call_next(request)
    
    # Log da resposta
    process_time = time.time() - start_time
    logger.info(
        f"🟢 RESPONSE: {response.status_code} - {process_time:.3f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
            "request_id": getattr(request.state, 'request_id', None)
        }
    )
    
    # Adiciona tempo de processamento no header
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 3. Middleware de autenticação customizado
app.add_middleware(AuthMiddleware)

# 4. Compressão GZIP para respostas grandes
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 5. CORS - configurado dinamicamente
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# ===== HANDLERS DE EXCEÇÃO =====
register_exception_handlers(app)

# ===== ROUTERS MODULARES =====

# Health check endpoint (sempre disponível)
@app.get("/health", tags=["Sistema"], summary="Verificação de saúde da API")
async def health_check():
    """
    Endpoint para verificação de status da API.
    Usado para monitoramento e load balancers.
    """
    return {
        "status": "healthy",
        "service": "Fluyt Comercial API",
        "version": settings.api_version,
        "environment": settings.environment,
        "timestamp": time.time()
    }

# Root endpoint com informações básicas
@app.get("/", tags=["Sistema"], summary="Informações da API")
async def root():
    """Informações básicas sobre a API"""
    return {
        "message": "Fluyt Comercial API",
        "version": settings.api_version,
        "docs": f"/api/{settings.api_version}/docs" if not settings.is_production else None,
        "health": "/health"
    }

# Registro de routers modulares
# Prefixo padrão para versionamento: /api/v1

prefix = f"/api/{settings.api_version}"

# ===== IMPORTAÇÃO DINÂMICA DOS ROUTERS =====
# Cada módulo deve ter um arquivo controller.py com uma variável 'router'

try:
    # Módulo de Autenticação (sem autenticação obrigatória)
    from modules.equipe.controller import router as equipe_router
    app.include_router(equipe_router, prefix=f"{prefix}/auth", tags=["🔐 Autenticação"])

    # Módulos principais (requerem autenticação)
    from modules.clientes.controller import router as clientes_router
    app.include_router(clientes_router, prefix=f"{prefix}/clientes", tags=["👥 Clientes"])

    from modules.ambientes.controller import router as ambientes_router
    app.include_router(ambientes_router, prefix=f"{prefix}/ambientes", tags=["🏠 Ambientes"])

    from modules.orcamentos.controller import router as orcamentos_router
    app.include_router(orcamentos_router, prefix=f"{prefix}/orcamentos", tags=["💰 Orçamentos"])

    from modules.aprovacoes.controller import router as aprovacoes_router
    app.include_router(aprovacoes_router, prefix=f"{prefix}/aprovacoes", tags=["✅ Aprovações"])

    from modules.contratos.controller import router as contratos_router
    app.include_router(contratos_router, prefix=f"{prefix}/contratos", tags=["📄 Contratos"])

    from modules.configuracoes.controller import router as configuracoes_router
    app.include_router(configuracoes_router, prefix=f"{prefix}/configuracoes", tags=["⚙️ Configurações"])

    from modules.montadores.controller import router as montadores_router
    app.include_router(montadores_router, prefix=f"{prefix}/montadores", tags=["🔧 Montadores"])

    from modules.transportadoras.controller import router as transportadoras_router
    app.include_router(transportadoras_router, prefix=f"{prefix}/transportadoras", tags=["🚛 Transportadoras"])

    from modules.status_orcamento.controller import router as status_router
    app.include_router(status_router, prefix=f"{prefix}/status", tags=["📊 Status"])

    # Módulos de sistema
    from modules.xml_logs.controller import router as xml_logs_router
    app.include_router(xml_logs_router, prefix=f"{prefix}/xml-logs", tags=["📋 Logs XML"])

    from modules.auditoria.controller import router as auditoria_router
    app.include_router(auditoria_router, prefix=f"{prefix}/auditoria", tags=["🔍 Auditoria"])

    # ⚠️ ENDPOINTS TEMPORÁRIOS DE TESTE - SEM AUTENTICAÇÃO!
    if settings.is_development:
        from modules.test_endpoints.routes import router as test_router
        app.include_router(test_router, prefix=f"{prefix}", tags=["🚨 TESTE TEMPORÁRIO"])
        logger.warning("🚨 ENDPOINTS DE TESTE TEMPORÁRIOS ATIVADOS - REMOVER EM PRODUÇÃO!")

    logger.info("✅ Todos os routers modulares carregados com sucesso")

except ImportError as e:
    logger.warning(f"⚠️ Alguns módulos ainda não implementados: {e}")
    # Em desenvolvimento, alguns módulos podem não existir ainda

# ===== MIDDLEWARE DE DESENVOLVIMENTO =====
if settings.is_development:
    @app.middleware("http")
    async def debug_headers(request: Request, call_next):
        """Adiciona headers de debug em desenvolvimento"""
        response = await call_next(request)
        response.headers["X-Environment"] = "development"
        response.headers["X-Debug"] = "true"
        return response

# ===== EVENTOS DE STARTUP ADICIONAIS =====
@app.on_event("startup")
async def startup_event():
    """Configurações adicionais no startup"""
    logger.info("🔧 Executando configurações de startup...")
    
    # Aqui podem ser adicionadas tarefas como:
    # - Verificação de conectividade com Supabase
    # - Carregamento de cache inicial
    # - Inicialização de workers de background
    
    logger.info("✅ Startup concluído com sucesso!")

# ===== CONFIGURAÇÃO FINAL =====
if __name__ == "__main__":
    import uvicorn
    
    # Configuração para execução direta (desenvolvimento)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True
    )
