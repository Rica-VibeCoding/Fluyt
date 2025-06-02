"""
Controller (rotas) para o módulo de Orçamentos.
Define endpoints REST para operações de orçamento.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from core.auth import get_current_user, require_admin, require_vendedor_ou_superior
from core.database import get_database
from supabase import Client
import uuid

from .schemas import (
    OrcamentoCreate,
    OrcamentoUpdate,
    OrcamentoResponse,
    OrcamentoListItem,
    OrcamentoFilters,
    SolicitacaoAprovacao,
    CalculoCustos,
    RelatorioMargem
)
from .services import OrcamentoService
from .repository import OrcamentoRepository

# Router para o módulo de orçamentos
router = APIRouter()


@router.post("/", 
    response_model=OrcamentoResponse,
    summary="Criar novo orçamento",
    description="Cria um novo orçamento com ambientes, plano de pagamento e custos"
)
async def criar_orcamento(
    orcamento_data: OrcamentoCreate,
    current_user: Dict[str, Any] = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Cria um novo orçamento.
    
    - **Todos os ambientes** são incluídos automaticamente
    - **Calcula custos** automaticamente baseado nas configurações da loja
    - **Verifica limites de desconto** e solicita aprovação se necessário
    - **Gera numeração** automática para o orçamento
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.criar_orcamento(orcamento_data, current_user)


@router.get("/",
    response_model=List[OrcamentoListItem],
    summary="Listar orçamentos",
    description="Lista orçamentos da loja com filtros e paginação"
)
async def listar_orcamentos(
    # Filtros opcionais
    cliente_nome: Optional[str] = Query(None, description="Filtro por nome do cliente"),
    vendedor_id: Optional[uuid.UUID] = Query(None, description="Filtro por vendedor"),
    status_id: Optional[uuid.UUID] = Query(None, description="Filtro por status"),
    necessita_aprovacao: Optional[bool] = Query(None, description="Apenas orçamentos pendentes de aprovação"),
    valor_minimo: Optional[float] = Query(None, ge=0, description="Valor mínimo"),
    valor_maximo: Optional[float] = Query(None, ge=0, description="Valor máximo"),
    
    # Paginação
    skip: int = Query(0, ge=0, description="Registros a pular"),
    limit: int = Query(50, ge=1, le=200, description="Limite de registros"),
    
    # Dependências
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """
    Lista orçamentos com filtros aplicados.
    
    **Regras de acesso:**
    - **Vendedor:** Vê apenas seus próprios orçamentos
    - **Gerente:** Vê orçamentos de toda a equipe da loja
    - **Admin Master:** Vê orçamentos de todas as lojas
    """
    # Constrói filtros
    filters = OrcamentoFilters(
        cliente_nome=cliente_nome,
        vendedor_id=vendedor_id,
        status_id=status_id,
        necessita_aprovacao=necessita_aprovacao,
        valor_minimo=valor_minimo,
        valor_maximo=valor_maximo
    )
    
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.listar_orcamentos(filters, current_user, skip, limit)


@router.get("/{orcamento_id}",
    response_model=OrcamentoResponse,
    summary="Obter orçamento por ID",
    description="Retorna detalhes completos de um orçamento específico"
)
async def obter_orcamento(
    orcamento_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """
    Obtém detalhes de um orçamento específico.
    
    **Dados retornados variam por perfil:**
    - **Vendedor/Gerente:** Valores e dados básicos (sem custos detalhados)
    - **Admin Master:** Todos os dados incluindo custos e margem
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.obter_orcamento(orcamento_id, current_user)


@router.put("/{orcamento_id}",
    response_model=OrcamentoResponse,
    summary="Atualizar orçamento",
    description="Atualiza dados de um orçamento existente"
)
async def atualizar_orcamento(
    orcamento_id: uuid.UUID,
    orcamento_data: OrcamentoUpdate,
    current_user: Dict[str, Any] = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Atualiza um orçamento existente.
    
    - **Recalcula custos** automaticamente
    - **Verifica permissões** de edição
    - **Solicita nova aprovação** se o desconto for alterado
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.atualizar_orcamento(orcamento_id, orcamento_data, current_user)


@router.delete("/{orcamento_id}",
    summary="Excluir orçamento",
    description="Exclui um orçamento (soft delete)"
)
async def excluir_orcamento(
    orcamento_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Exclui um orçamento.
    
    **Regras:**
    - Apenas orçamentos em status "Negociação" podem ser excluídos
    - Vendedor só pode excluir seus próprios orçamentos
    - Gerente pode excluir orçamentos da equipe
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    await service.excluir_orcamento(orcamento_id, current_user)
    return {"message": "Orçamento excluído com sucesso"}


@router.post("/{orcamento_id}/solicitar-aprovacao",
    summary="Solicitar aprovação de desconto",
    description="Solicita aprovação para desconto acima do limite do usuário"
)
async def solicitar_aprovacao(
    orcamento_id: uuid.UUID,
    solicitacao: SolicitacaoAprovacao,
    current_user: Dict[str, Any] = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Solicita aprovação para desconto superior ao limite.
    
    **Fluxo de aprovação:**
    1. Vendedor → Gerente (até 25%)
    2. Gerente → Admin Master (acima de 25%)
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.solicitar_aprovacao(orcamento_id, solicitacao, current_user)


@router.post("/{orcamento_id}/aprovar",
    summary="Aprovar/Rejeitar desconto",
    description="Aprova ou rejeita uma solicitação de desconto"
)
async def processar_aprovacao(
    orcamento_id: uuid.UUID,
    aprovado: bool = Query(..., description="True para aprovar, False para rejeitar"),
    justificativa: Optional[str] = Query(None, description="Justificativa da decisão"),
    current_user: Dict[str, Any] = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Processa uma solicitação de aprovação.
    
    **Apenas aprovadores válidos** podem usar este endpoint.
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.processar_aprovacao(orcamento_id, aprovado, justificativa, current_user)


@router.get("/{orcamento_id}/calcular-custos",
    response_model=CalculoCustos,
    summary="Calcular custos do orçamento",
    description="Calcula custos detalhados (apenas Admin Master)"
)
async def calcular_custos(
    orcamento_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(require_admin()),
    db: Client = Depends(get_database)
):
    """
    Retorna cálculo detalhado de custos de um orçamento.
    
    **Acesso restrito:** Apenas Admin Master pode ver custos detalhados.
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.calcular_custos_detalhado(orcamento_id, current_user)


@router.post("/{orcamento_id}/duplicar",
    response_model=OrcamentoResponse,
    summary="Duplicar orçamento",
    description="Cria uma cópia de um orçamento existente"
)
async def duplicar_orcamento(
    orcamento_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Duplica um orçamento existente.
    
    - Mantém todos os dados exceto número e data
    - Útil para orçamentos similares ao mesmo cliente
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.duplicar_orcamento(orcamento_id, current_user)


# ===== RELATÓRIOS =====

@router.get("/relatorios/margem",
    response_model=List[RelatorioMargem],
    summary="Relatório de margem",
    description="Relatório detalhado de margem por orçamento (Admin Master apenas)"
)
async def relatorio_margem(
    # Filtros de período
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    
    # Filtros específicos
    vendedor_id: Optional[uuid.UUID] = Query(None, description="Filtro por vendedor"),
    loja_id: Optional[uuid.UUID] = Query(None, description="Filtro por loja (Admin Master)"),
    
    # Paginação
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    
    # Dependências
    current_user: Dict[str, Any] = Depends(require_admin()),
    db: Client = Depends(get_database)
):
    """
    Gera relatório detalhado de margem e lucratividade.
    
    **Acesso restrito:** Apenas Admin Master.
    **Dados incluídos:** Custos completos, margem líquida, percentual de margem.
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.relatorio_margem(
        data_inicio, data_fim, vendedor_id, loja_id, 
        current_user, skip, limit
    )


@router.get("/dashboard/metricas",
    summary="Métricas do dashboard",
    description="Métricas resumidas para dashboard (por perfil)"
)
async def metricas_dashboard(
    periodo_dias: int = Query(30, ge=1, le=365, description="Período em dias"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """
    Retorna métricas resumidas para o dashboard.
    
    **Dados variam por perfil:**
    - **Vendedor:** Apenas suas métricas
    - **Gerente:** Métricas da equipe
    - **Admin Master:** Métricas consolidadas
    """
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.obter_metricas_dashboard(periodo_dias, current_user)


# ===== ENDPOINTS DE APOIO =====

@router.get("/status-disponiveis",
    summary="Status disponíveis",
    description="Lista status configurados para a loja"
)
async def listar_status_disponiveis(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """Lista todos os status configurados para a loja do usuário."""
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.listar_status_disponiveis(current_user)


@router.get("/{orcamento_id}/historico-aprovacoes",
    summary="Histórico de aprovações",
    description="Lista histórico de aprovações de um orçamento"
)
async def historico_aprovacoes(
    orcamento_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """Retorna histórico completo de aprovações de um orçamento."""
    repository = OrcamentoRepository(db)
    service = OrcamentoService(repository)
    return await service.obter_historico_aprovacoes(orcamento_id, current_user)
