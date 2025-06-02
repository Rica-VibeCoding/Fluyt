"""
Controller (rotas) para o módulo de Clientes.
Define endpoints REST para operações de cliente.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from core.auth import get_current_user, require_vendedor_ou_superior
from core.database import get_database
from supabase import Client
import uuid

from .schemas import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteListItem,
    ClienteBusca,
    TipoVenda
)
from .services import ClienteService
from .repository import ClienteRepository

# Router para o módulo de clientes
router = APIRouter(prefix='/clientes', tags=['clientes'])


@router.post("/",
    response_model=ClienteResponse,
    summary="Criar novo cliente",
    description="Cria um novo cliente na loja"
)
async def criar_cliente(
    cliente_data: ClienteCreate,
    current_user: dict = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Cria um novo cliente.
    
    - **Validação automática** de CPF/CNPJ únicos por loja
    - **RLS aplicado** automaticamente (cliente vinculado à loja do usuário)
    - **Campos obrigatórios:** Nome
    - **Campos opcionais:** CPF/CNPJ, contatos, endereço
    """
    repository = ClienteRepository(db)
    service = ClienteService(repository)
    return await service.criar_cliente(cliente_data, current_user)


@router.get("/",
    response_model=List[ClienteListItem],
    summary="Listar clientes",
    description="Lista clientes da loja com filtros e paginação"
)
async def listar_clientes(
    # Filtros opcionais
    nome: Optional[str] = Query(None, description="Filtro por nome do cliente"),
    tipo_venda: Optional[TipoVenda] = Query(None, description="Filtro por tipo de venda"),
    
    # Paginação
    skip: int = Query(0, ge=0, description="Registros a pular"),
    limit: int = Query(50, ge=1, le=200, description="Limite de registros"),
    
    # Dependências
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """
    Lista clientes da loja com filtros aplicados.
    
    **Filtros disponíveis:**
    - **Nome:** Busca parcial no nome do cliente
    - **Tipo de venda:** NORMAL ou FUTURA
    
    **Ordenação:** Data de criação (mais recentes primeiro)
    """
    repository = ClienteRepository(db)
    service = ClienteService(repository)
    return await service.listar_clientes(
        current_user, 
        skip, 
        limit, 
        filtro_nome=nome, 
        filtro_tipo=tipo_venda.value if tipo_venda else None
    )


@router.get("/buscar",
    response_model=List[ClienteBusca],
    summary="Buscar clientes",
    description="Busca clientes por termo (nome, CPF, telefone)"
)
async def buscar_clientes(
    termo: str = Query(..., min_length=2, description="Termo de busca"),
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """
    Busca clientes por termo em múltiplos campos.
    
    **Campos de busca:**
    - Nome do cliente
    - CPF/CNPJ
    - Telefone
    
    **Limite:** 20 resultados máximo
    **Uso:** Ideal para autocompletar ou seleção rápida
    """
    repository = ClienteRepository(db)
    service = ClienteService(repository)
    return await service.buscar_clientes(termo, current_user)


@router.get("/{cliente_id}",
    response_model=ClienteResponse,
    summary="Obter cliente por ID",
    description="Retorna detalhes completos de um cliente específico"
)
async def obter_cliente(
    cliente_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_database)
):
    """
    Obtém detalhes completos de um cliente.
    
    **Permissões:**
    - **Usuários da loja:** Veem apenas clientes da própria loja
    - **Admin Master:** Vê clientes de todas as lojas
    """
    repository = ClienteRepository(db)
    service = ClienteService(repository)
    return await service.obter_cliente(cliente_id, current_user)


@router.put("/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente",
    description="Atualiza dados de um cliente existente"
)
async def atualizar_cliente(
    cliente_id: uuid.UUID,
    cliente_data: ClienteUpdate,
    current_user: dict = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Atualiza um cliente existente.
    
    - **Validação automática** de CPF/CNPJ únicos se alterado
    - **Campos opcionais:** Apenas campos fornecidos são atualizados
    - **Histórico:** Timestamp de atualização automático
    """
    repository = ClienteRepository(db)
    service = ClienteService(repository)
    return await service.atualizar_cliente(cliente_id, cliente_data, current_user)


@router.delete("/{cliente_id}",
    summary="Excluir cliente",
    description="Exclui um cliente (soft delete)"
)
async def excluir_cliente(
    cliente_id: uuid.UUID,
    current_user: dict = Depends(require_vendedor_ou_superior()),
    db: Client = Depends(get_database)
):
    """
    Exclui um cliente.
    
    **Regras de negócio:**
    - **Soft delete:** Cliente é marcado como inativo
    - **Proteção:** Clientes com orçamentos não podem ser excluídos
    - **Permissões:** Apenas usuários da mesma loja (+ Admin Master)
    """
    repository = ClienteRepository(db)
    service = ClienteService(repository)
    await service.excluir_cliente(cliente_id, current_user)
    return {"message": "Cliente excluído com sucesso"}
