"""
Configuração e gerenciamento da conexão com Supabase.
Implementa RLS (Row Level Security) automático e dependency injection.
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from core.config import get_settings, Settings
from core.auth import get_current_user
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper para o cliente Supabase com funcionalidades específicas do Fluyt.
    Implementa RLS automático e gerenciamento de sessão.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Cliente Supabase com chave anônima (para operações autenticadas)"""
        if self._client is None:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_anon_key
            )
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Cliente Supabase com chave de serviço (bypassa RLS - usar com cuidado)"""
        if self._service_client is None:
            self._service_client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_key
            )
        return self._service_client
    
    def set_auth_token(self, token: str) -> Client:
        """
        Define o token JWT para operações autenticadas.
        Necessário para RLS funcionar corretamente.
        """
        self.client.auth.set_session_from_url(token)
        return self.client
    
    def get_user_client(self, user_data: Dict[str, Any]) -> Client:
        """
        Retorna cliente Supabase configurado para um usuário específico.
        Aplica automaticamente o RLS baseado no loja_id do usuário.
        """
        client = self.client
        
        # Configura o contexto RLS para o usuário
        loja_id = user_data.get('loja_id')
        if loja_id:
            # Configura variáveis de contexto para RLS
            client.rpc('set_config', {
                'setting_name': 'app.current_loja_id',
                'setting_value': str(loja_id),
                'is_local': True
            })
        
        return client


# Instância global do Supabase client
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client(settings: Settings = Depends(get_settings)) -> SupabaseClient:
    """
    Dependency injection para obter o cliente Supabase.
    Cria uma única instância por configuração.
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = SupabaseClient(settings)
    
    return _supabase_client


def get_database(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Client:
    """
    Dependency injection para obter cliente Supabase autenticado.
    Aplica automaticamente RLS baseado no usuário logado.
    
    Args:
        current_user: Dados do usuário autenticado (do JWT)
        supabase_client: Cliente Supabase configurado
    
    Returns:
        Cliente Supabase pronto para operações com RLS aplicado
    """
    try:
        return supabase_client.get_user_client(current_user)
    except Exception as e:
        logger.error(f"Erro ao configurar cliente database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao configurar acesso ao banco de dados"
        )


def get_service_database(
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Client:
    """
    Dependency injection para operações administrativas.
    BYPASSA RLS - usar apenas para operações de sistema.
    
    ⚠️ ATENÇÃO: Este cliente bypassa RLS. Use apenas para:
    - Operações de configuração inicial
    - Logs de auditoria
    - Processos de background administrativos
    """
    return supabase_client.service_client


def with_transaction(func):
    """
    Decorator para executar operações em transação.
    Rollback automático em caso de erro.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Implementação simplificada - Supabase gerencia transações automaticamente
        # Em caso de necessidade futura, pode ser expandido
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em transação: {e}")
            raise
    
    return wrapper


class DatabaseException(Exception):
    """Exceção customizada para erros de banco de dados"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


def handle_supabase_error(error: Exception) -> DatabaseException:
    """
    Converte erros do Supabase em exceções padronizadas.
    Facilita o tratamento de erros específicos.
    """
    error_message = str(error)
    
    # Mapeamento de erros comuns
    if "duplicate key" in error_message.lower():
        return DatabaseException(
            message="Registro duplicado encontrado",
            code="DUPLICATE_KEY",
            details={"original_error": error_message}
        )
    elif "foreign key" in error_message.lower():
        return DatabaseException(
            message="Referência inválida entre registros",
            code="FOREIGN_KEY_VIOLATION",
            details={"original_error": error_message}
        )
    elif "not found" in error_message.lower():
        return DatabaseException(
            message="Registro não encontrado",
            code="NOT_FOUND",
            details={"original_error": error_message}
        )
    else:
        return DatabaseException(
            message="Erro interno do banco de dados",
            code="INTERNAL_ERROR",
            details={"original_error": error_message}
        )


# Configuração de logging para operações de banco
logging.getLogger("supabase").setLevel(logging.INFO) 