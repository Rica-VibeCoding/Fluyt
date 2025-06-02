# FastAPI/Pydantic models for clientes

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class TipoVenda(str, Enum):
    """Tipos de venda disponíveis"""
    NORMAL = "NORMAL"
    FUTURA = "FUTURA"


# ===== SCHEMAS DE ENTRADA (REQUEST) =====

class ClienteCreate(BaseModel):
    """Schema para criação de cliente"""
    nome: str = Field(..., min_length=2, max_length=255, description="Nome completo do cliente")
    cpf_cnpj: Optional[str] = Field(None, max_length=20, description="CPF ou CNPJ do cliente")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone de contato")
    email: Optional[str] = Field(None, max_length=255, description="Email do cliente")
    endereco: Optional[str] = Field(None, max_length=500, description="Endereço completo")
    cidade: Optional[str] = Field(None, max_length=100, description="Cidade")
    cep: Optional[str] = Field(None, max_length=10, description="CEP")
    tipo_venda: Optional[TipoVenda] = Field(default=TipoVenda.NORMAL, description="Tipo de venda")
    observacao: Optional[str] = Field(None, max_length=1000, description="Observações gerais")
    
    @validator('cpf_cnpj')
    def validar_cpf_cnpj(cls, v):
        """Remove formatação do CPF/CNPJ"""
        if v:
            # Remove caracteres especiais
            return ''.join(char for char in v if char.isdigit())
        return v
    
    @validator('email')
    def validar_email(cls, v):
        """Validação básica de email"""
        if v and '@' not in v:
            raise ValueError('Email deve conter @')
        return v


class ClienteUpdate(BaseModel):
    """Schema para atualização de cliente"""
    nome: Optional[str] = Field(None, min_length=2, max_length=255, description="Nome completo do cliente")
    cpf_cnpj: Optional[str] = Field(None, max_length=20, description="CPF ou CNPJ do cliente")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone de contato")
    email: Optional[str] = Field(None, max_length=255, description="Email do cliente")
    endereco: Optional[str] = Field(None, max_length=500, description="Endereço completo")
    cidade: Optional[str] = Field(None, max_length=100, description="Cidade")
    cep: Optional[str] = Field(None, max_length=10, description="CEP")
    tipo_venda: Optional[TipoVenda] = Field(None, description="Tipo de venda")
    observacao: Optional[str] = Field(None, max_length=1000, description="Observações gerais")
    
    @validator('cpf_cnpj')
    def validar_cpf_cnpj(cls, v):
        """Remove formatação do CPF/CNPJ"""
        if v:
            return ''.join(char for char in v if char.isdigit())
        return v
    
    @validator('email')
    def validar_email(cls, v):
        """Validação básica de email"""
        if v and '@' not in v:
            raise ValueError('Email deve conter @')
        return v


# ===== SCHEMAS DE SAÍDA (RESPONSE) =====

class ClienteResponse(BaseModel):
    """Schema de resposta para cliente"""
    id: uuid.UUID
    nome: str
    cpf_cnpj: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    endereco: Optional[str]
    cidade: Optional[str]
    cep: Optional[str]
    loja_id: uuid.UUID
    tipo_venda: TipoVenda
    observacao: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClienteListItem(BaseModel):
    """Schema simplificado para listagem de clientes"""
    id: uuid.UUID
    nome: str
    cpf_cnpj: Optional[str]
    telefone: Optional[str]
    tipo_venda: TipoVenda
    cidade: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClienteBusca(BaseModel):
    """Schema para resultado de busca de cliente"""
    id: uuid.UUID
    nome: str
    cpf_cnpj: Optional[str]
    telefone: Optional[str]
    cidade: Optional[str]
    
    class Config:
        from_attributes = True
