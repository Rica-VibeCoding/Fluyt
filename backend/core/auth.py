"""
Sistema de autenticação e autorização do Fluyt Comercial.
Implementa JWT com Supabase Auth e middleware para RLS.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Dict, Any, Optional, List
from core.config import get_settings, Settings
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Esquema de autenticação Bearer
security = HTTPBearer()


class PerfilUsuario(str, Enum):
    """Enum dos perfis de usuário no sistema"""
    VENDEDOR = "VENDEDOR"
    GERENTE = "GERENTE"
    MEDIDOR = "MEDIDOR"
    ADMIN_MASTER = "ADMIN_MASTER"


class AuthException(Exception):
    """Exceção customizada para erros de autenticação"""
    
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


def decode_jwt_token(token: str, settings: Settings) -> Dict[str, Any]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT para decodificar
        settings: Configurações da aplicação
    
    Returns:
        Payload decodificado do token
    
    Raises:
        AuthException: Se o token for inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Validações básicas
        if payload.get("exp") is None:
            raise AuthException("Token sem data de expiração")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthException("Token sem identificação de usuário")
        
        return payload
        
    except JWTError as e:
        logger.warning(f"Token JWT inválido: {e}")
        raise AuthException("Token inválido ou expirado")
    except Exception as e:
        logger.error(f"Erro ao decodificar token: {e}")
        raise AuthException("Erro interno de autenticação")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Dependency injection para obter o usuário autenticado.
    Valida o token JWT e retorna os dados do usuário.
    
    Returns:
        Dados do usuário autenticado incluindo:
        - user_id: UUID do usuário
        - loja_id: UUID da loja (para RLS)
        - perfil: Perfil do usuário
        - email: Email do usuário
    
    Raises:
        HTTPException: Se a autenticação falhar
    """
    try:
        token = credentials.credentials
        payload = decode_jwt_token(token, settings)
        
        # Extrai dados essenciais do payload
        user_data = {
            "user_id": payload.get("sub"),
            "loja_id": payload.get("loja_id"),
            "perfil": payload.get("perfil"),
            "email": payload.get("email"),
            "nome": payload.get("nome", ""),
            "token": token  # Mantém token para operações com Supabase
        }
        
        # Validações obrigatórias
        if not user_data["loja_id"]:
            raise AuthException("Usuário sem loja associada")
        
        if not user_data["perfil"]:
            raise AuthException("Usuário sem perfil definido")
        
        return user_data
        
    except AuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Erro inesperado na autenticação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno de autenticação"
        )


def require_perfil(perfis_permitidos: List[PerfilUsuario]):
    """
    Decorator para restringir acesso por perfil de usuário.
    
    Args:
        perfis_permitidos: Lista de perfis que podem acessar o endpoint
    
    Returns:
        Dependency function para usar em rotas FastAPI
    """
    def perfil_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_perfil = current_user.get("perfil")
        
        if user_perfil not in [p.value for p in perfis_permitidos]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfis permitidos: {[p.value for p in perfis_permitidos]}"
            )
        
        return current_user
    
    return perfil_dependency


def require_admin():
    """Dependency que exige perfil ADMIN_MASTER"""
    return require_perfil([PerfilUsuario.ADMIN_MASTER])


def require_gerente_ou_admin():
    """Dependency que exige perfil GERENTE ou ADMIN_MASTER"""
    return require_perfil([PerfilUsuario.GERENTE, PerfilUsuario.ADMIN_MASTER])


def require_vendedor_ou_superior():
    """Dependency que exige qualquer perfil exceto MEDIDOR"""
    return require_perfil([
        PerfilUsuario.VENDEDOR,
        PerfilUsuario.GERENTE,
        PerfilUsuario.ADMIN_MASTER
    ])


class AuthMiddleware:
    """
    Middleware de autenticação para configurar contexto de usuário.
    Prepara dados necessários para RLS automático.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extrai token se presente
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
                try:
                    settings = get_settings()
                    payload = decode_jwt_token(token, settings)
                    
                    # Adiciona dados do usuário ao escopo da requisição
                    scope["user"] = {
                        "user_id": payload.get("sub"),
                        "loja_id": payload.get("loja_id"),
                        "perfil": payload.get("perfil"),
                        "token": token
                    }
                    
                except AuthException:
                    # Token inválido - continua sem usuário
                    scope["user"] = None
        
        await self.app(scope, receive, send)


def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Obtém usuário opcional (não obrigatório).
    Útil para endpoints que funcionam com ou sem autenticação.
    """
    return getattr(request.scope, "user", None)


def create_access_token(user_data: Dict[str, Any], settings: Settings) -> str:
    """
    Cria um token JWT para um usuário.
    
    Args:
        user_data: Dados do usuário para incluir no token
        settings: Configurações da aplicação
    
    Returns:
        Token JWT codificado
    """
    from datetime import datetime, timedelta
    
    # Dados obrigatórios no token
    payload = {
        "sub": str(user_data["user_id"]),
        "loja_id": str(user_data["loja_id"]),
        "perfil": user_data["perfil"],
        "email": user_data["email"],
        "nome": user_data.get("nome", ""),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    }
    
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# Função para verificar se usuário pode acessar loja específica
def verificar_acesso_loja(current_user: Dict[str, Any], loja_id: str) -> bool:
    """
    Verifica se o usuário tem acesso a uma loja específica.
    
    Args:
        current_user: Dados do usuário autenticado
        loja_id: ID da loja a verificar
    
    Returns:
        True se tem acesso, False caso contrário
    """
    user_loja_id = current_user.get("loja_id")
    user_perfil = current_user.get("perfil")
    
    # Admin Master tem acesso a todas as lojas
    if user_perfil == PerfilUsuario.ADMIN_MASTER.value:
        return True
    
    # Outros perfis só acessam sua própria loja
    return str(user_loja_id) == str(loja_id)


def assert_acesso_loja(current_user: Dict[str, Any], loja_id: str) -> None:
    """
    Valida acesso à loja ou lança exceção.
    
    Args:
        current_user: Dados do usuário autenticado
        loja_id: ID da loja a verificar
    
    Raises:
        HTTPException: Se não tem acesso à loja
    """
    if not verificar_acesso_loja(current_user, loja_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta loja"
        )
