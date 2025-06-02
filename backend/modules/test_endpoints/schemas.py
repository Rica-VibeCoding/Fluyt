"""
Schemas para endpoints de teste temporários.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum

class TipoVenda(str, Enum):
    NORMAL = "NORMAL"
    FUTURA = "FUTURA"

class TestClienteCreate(BaseModel):
    """Schema para criar cliente em teste"""
    nome: str = Field(..., min_length=1, max_length=255)
    cpf_cnpj: str = Field(..., min_length=11, max_length=18)
    telefone: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    endereco: str = Field(..., min_length=5, max_length=500)
    cidade: str = Field(..., min_length=2, max_length=100)
    cep: str = Field(..., min_length=8, max_length=9)
    loja_id: str = Field(..., description="ID da loja (D-Art ou Romanza)")
    tipo_venda: TipoVenda = TipoVenda.NORMAL
    observacao: Optional[str] = None

    @validator('cpf_cnpj')
    def validate_cpf_cnpj(cls, v):
        # Remove caracteres especiais
        v = ''.join(filter(str.isdigit, v))
        if len(v) not in [11, 14]:
            raise ValueError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos')
        return v

    @validator('cep')
    def validate_cep(cls, v):
        # Remove caracteres especiais
        v = ''.join(filter(str.isdigit, v))
        if len(v) != 8:
            raise ValueError('CEP deve ter 8 dígitos')
        return v

class TestAmbienteCreate(BaseModel):
    """Schema para criar ambiente em teste"""
    nome_ambiente: str = Field(..., min_length=1, max_length=255)
    nome_cliente: str = Field(..., min_length=1, max_length=255)
    valor_total: Decimal = Field(..., gt=0, description="Valor deve ser positivo")
    linha_produto: str = Field(..., min_length=1, max_length=100)
    descricao_completa: Optional[str] = None
    detalhes_xml: Optional[Dict[str, Any]] = {}
    loja_id: str = Field(..., description="ID da loja")

class TestOrcamentoCreate(BaseModel):
    """Schema para criar orçamento em teste"""
    cliente_id: str = Field(..., description="ID do cliente")
    vendedor_id: str = Field(..., description="ID do vendedor")
    loja_id: str = Field(..., description="ID da loja")
    ambientes_ids: List[str] = Field(..., min_items=1, description="Lista de IDs dos ambientes")
    desconto_percentual: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    medidor_selecionado_id: Optional[str] = None
    montador_selecionado_id: Optional[str] = None
    transportadora_selecionada_id: Optional[str] = None
    custos_adicionais: Optional[List[Dict[str, Any]]] = []

class TestCalculoEngine(BaseModel):
    """Schema para testar engine de cálculo isoladamente"""
    valor_ambientes: Decimal = Field(..., gt=0)
    desconto_percentual: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    loja_id: str = Field(..., description="ID da loja para buscar configurações")
    vendedor_id: str = Field(..., description="ID do vendedor para comissão")
    custos_adicionais: Optional[List[Dict[str, Any]]] = []

class TestResponse(BaseModel):
    """Schema de resposta padrão para testes"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

class TestRLSValidation(BaseModel):
    """Schema para testar isolamento RLS"""
    loja_origem: str = Field(..., description="Loja que está fazendo a consulta")
    loja_destino: str = Field(..., description="Loja que está sendo consultada")
    recurso: str = Field(..., description="Recurso sendo acessado (clientes, orcamentos, etc.)")

class TestValidationError(BaseModel):
    """Schema para testar validações com dados inválidos"""
    campo: str
    valor_invalido: Any
    erro_esperado: str 