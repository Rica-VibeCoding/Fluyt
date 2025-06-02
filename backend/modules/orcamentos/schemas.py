"""
Schemas Pydantic para o módulo de Orçamentos.
Define modelos de validação para entrada e saída de dados.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum
import uuid


class StatusOrcamento(str, Enum):
    """Status possíveis para um orçamento"""
    NEGOCIACAO = "NEGOCIACAO"
    VENDIDO = "VENDIDO"
    FUTURA = "FUTURA"
    PERDIDO = "PERDIDO"


class TipoFormaPagamento(str, Enum):
    """Formas de pagamento disponíveis"""
    PIX = "PIX"
    BOLETO = "BOLETO"
    CARTAO = "CARTAO"
    DINHEIRO = "DINHEIRO"
    FINANCIAMENTO = "FINANCIAMENTO"


# ===== SCHEMAS DE ENTRADA (REQUEST) =====

class ParcellaPagamento(BaseModel):
    """Schema para definir uma parcela do plano de pagamento"""
    descricao: str = Field(..., description="Descrição da parcela (ex: 'Entrada', '1ª parcela')")
    valor: Decimal = Field(..., gt=0, description="Valor da parcela")
    data_vencimento: datetime = Field(..., description="Data de vencimento")
    forma_pagamento: TipoFormaPagamento = Field(..., description="Forma de pagamento")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações da parcela")


class CustoAdicional(BaseModel):
    """Schema para custos adicionais específicos do orçamento"""
    descricao_custo: str = Field(..., max_length=255, description="Descrição do custo adicional")
    valor_custo: Decimal = Field(..., gt=0, description="Valor do custo adicional")


class OrcamentoCreate(BaseModel):
    """Schema para criação de orçamento"""
    cliente_id: uuid.UUID = Field(..., description="ID do cliente")
    ambiente_ids: List[uuid.UUID] = Field(..., min_items=1, description="IDs dos ambientes (obrigatório pelo menos 1)")
    desconto_percentual: Decimal = Field(default=0, ge=0, le=100, description="Percentual de desconto aplicado")
    
    # Seleções obrigatórias
    medidor_selecionado_id: uuid.UUID = Field(..., description="ID do medidor selecionado")
    montador_selecionado_id: uuid.UUID = Field(..., description="ID do montador selecionado")
    transportadora_selecionada_id: uuid.UUID = Field(..., description="ID da transportadora selecionada")
    
    # Plano de pagamento
    plano_pagamento: List[ParcellaPagamento] = Field(..., min_items=1, description="Plano de pagamento")
    
    # Custos adicionais (opcional)
    custos_adicionais: Optional[List[CustoAdicional]] = Field(default=[], description="Custos adicionais específicos")
    
    # Observações
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações gerais do orçamento")
    
    @validator('plano_pagamento')
    def validar_plano_pagamento(cls, v):
        """Valida se o plano de pagamento está consistente"""
        if not v:
            raise ValueError("Plano de pagamento é obrigatório")
        
        # Verifica se todas as parcelas têm valores positivos
        for parcela in v:
            if parcela.valor <= 0:
                raise ValueError("Todas as parcelas devem ter valor positivo")
        
        return v


class OrcamentoUpdate(BaseModel):
    """Schema para atualização de orçamento"""
    desconto_percentual: Optional[Decimal] = Field(None, ge=0, le=100, description="Novo percentual de desconto")
    medidor_selecionado_id: Optional[uuid.UUID] = Field(None, description="Novo medidor selecionado")
    montador_selecionado_id: Optional[uuid.UUID] = Field(None, description="Novo montador selecionado")
    transportadora_selecionada_id: Optional[uuid.UUID] = Field(None, description="Nova transportadora selecionada")
    plano_pagamento: Optional[List[ParcellaPagamento]] = Field(None, description="Novo plano de pagamento")
    custos_adicionais: Optional[List[CustoAdicional]] = Field(None, description="Custos adicionais atualizados")
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações atualizadas")


class SolicitacaoAprovacao(BaseModel):
    """Schema para solicitar aprovação de desconto"""
    desconto_solicitado: Decimal = Field(..., gt=0, le=100, description="Percentual de desconto solicitado")
    justificativa: str = Field(..., min_length=10, max_length=500, description="Justificativa para o desconto")


# ===== SCHEMAS DE SAÍDA (RESPONSE) =====

class AmbienteResumo(BaseModel):
    """Schema resumido de ambiente para exibição no orçamento"""
    id: uuid.UUID
    nome_ambiente: str
    valor_total: Decimal
    linha_produto: Optional[str]


class CustoAdicionalResponse(BaseModel):
    """Schema de resposta para custos adicionais"""
    id: uuid.UUID
    descricao_custo: str
    valor_custo: Decimal


class ResumoFinanceiro(BaseModel):
    """Schema para resumo financeiro do orçamento (visível apenas para perfis autorizados)"""
    valor_ambientes: Decimal
    desconto_aplicado: Decimal
    valor_final: Decimal
    
    # Custos (visível apenas para Admin Master)
    custo_fabrica: Optional[Decimal] = None
    comissao_vendedor: Optional[Decimal] = None
    comissao_gerente: Optional[Decimal] = None
    custo_medidor: Optional[Decimal] = None
    custo_montador: Optional[Decimal] = None
    custo_frete: Optional[Decimal] = None
    total_custos_adicionais: Optional[Decimal] = None
    margem_lucro: Optional[Decimal] = None


class OrcamentoResponse(BaseModel):
    """Schema de resposta completo para orçamento"""
    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID
    loja_id: uuid.UUID
    vendedor_id: uuid.UUID
    status_id: Optional[uuid.UUID]
    
    # Dados financeiros básicos (sempre visíveis)
    resumo_financeiro: ResumoFinanceiro
    
    # Ambientes incluídos
    ambientes: List[AmbienteResumo]
    
    # Custos adicionais
    custos_adicionais: List[CustoAdicionalResponse]
    
    # Plano de pagamento
    plano_pagamento: List[Dict[str, Any]]  # JSON do plano de pagamento
    
    # Aprovação
    necessita_aprovacao: bool
    aprovador_id: Optional[uuid.UUID]
    
    # Metadados
    observacoes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrcamentoListItem(BaseModel):
    """Schema simplificado para listagem de orçamentos"""
    id: uuid.UUID
    numero: str
    cliente_nome: str  # Nome do cliente (join)
    valor_final: Decimal
    status_nome: str  # Nome do status (join)
    necessita_aprovacao: bool
    vendedor_nome: str  # Nome do vendedor (join)
    created_at: datetime
    
    class Config:
        from_attributes = True


class CalculoCustos(BaseModel):
    """Schema para retorno do cálculo de custos"""
    valor_ambientes: Decimal
    desconto_percentual: Decimal
    valor_final: Decimal
    
    custo_fabrica: Decimal
    comissao_vendedor: Decimal
    comissao_gerente: Decimal
    custo_medidor: Decimal
    custo_montador: Decimal
    custo_frete: Decimal
    total_custos_adicionais: Decimal
    
    margem_lucro: Decimal
    percentual_margem: Decimal
    
    # Detalhamento das regras aplicadas
    detalhes_calculo: Dict[str, Any]


class AprovacaoResponse(BaseModel):
    """Schema para resposta de aprovação"""
    id: uuid.UUID
    aprovador_nome: str
    acao: str
    nivel_aprovacao: str
    valor_desconto: Decimal
    margem_resultante: Decimal
    justificativa: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== SCHEMAS DE FILTROS =====

class OrcamentoFilters(BaseModel):
    """Schema para filtros de busca de orçamentos"""
    cliente_nome: Optional[str] = Field(None, description="Filtro por nome do cliente")
    vendedor_id: Optional[uuid.UUID] = Field(None, description="Filtro por vendedor")
    status_id: Optional[uuid.UUID] = Field(None, description="Filtro por status")
    necessita_aprovacao: Optional[bool] = Field(None, description="Filtro por necessidade de aprovação")
    valor_minimo: Optional[Decimal] = Field(None, ge=0, description="Valor mínimo do orçamento")
    valor_maximo: Optional[Decimal] = Field(None, ge=0, description="Valor máximo do orçamento")
    data_inicio: Optional[datetime] = Field(None, description="Data de criação - início")
    data_fim: Optional[datetime] = Field(None, description="Data de criação - fim")
    
    @validator('data_fim')
    def validar_periodo(cls, v, values):
        """Valida se a data fim é posterior à data início"""
        if v and values.get('data_inicio') and v < values['data_inicio']:
            raise ValueError("Data fim deve ser posterior à data início")
        return v


# ===== SCHEMAS PARA RELATÓRIOS =====

class RelatorioMargem(BaseModel):
    """Schema para relatório de margem (Admin Master apenas)"""
    orcamento_id: uuid.UUID
    numero: str
    cliente_nome: str
    vendedor_nome: str
    valor_venda: Decimal
    custo_total: Decimal
    margem_liquida: Decimal
    percentual_margem: Decimal
    data_criacao: datetime
    
    # Detalhamento de custos
    detalhes_custos: Dict[str, Decimal]
    
    class Config:
        from_attributes = True
