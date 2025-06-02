"""
Sistema centralizado de tratamento de exceções do Fluyt Comercial.
Define exceções customizadas e handlers padronizados.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any, Dict, Optional
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class FluyteException(Exception):
    """Exceção base para todas as exceções customizadas do Fluyt"""
    
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessRuleException(FluyteException):
    """Exceção para violações de regras de negócio"""
    
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ValidationException(FluyteException):
    """Exceção para erros de validação de dados"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        details = details or {}
        if field:
            details["field"] = field
            
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class PermissionException(FluyteException):
    """Exceção para erros de permissão"""
    
    def __init__(self, message: str = "Acesso negado", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundException(FluyteException):
    """Exceção para recursos não encontrados"""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} não encontrado"
        if resource_id:
            message += f" (ID: {resource_id})"
            
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "resource_id": resource_id}
        )


class DuplicateResourceException(FluyteException):
    """Exceção para recursos duplicados"""
    
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            message=f"{resource} já existe com {field}: {value}",
            code="DUPLICATE_RESOURCE",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": value}
        )


class ExternalServiceException(FluyteException):
    """Exceção para erros em serviços externos"""
    
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"Erro no serviço {service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details or {"service": service}
        )


class XMLProcessingException(FluyteException):
    """Exceção específica para processamento de XML"""
    
    def __init__(self, message: str, filename: Optional[str] = None, details: Optional[Dict] = None):
        details = details or {}
        if filename:
            details["filename"] = filename
            
        super().__init__(
            message=f"Erro no processamento XML: {message}",
            code="XML_PROCESSING_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ConfigurationException(FluyteException):
    """Exceção para erros de configuração"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {"config_key": config_key} if config_key else {}
        
        super().__init__(
            message=f"Erro de configuração: {message}",
            code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


def create_error_response(
    message: str,
    code: str = "INTERNAL_ERROR",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria resposta de erro padronizada.
    
    Args:
        message: Mensagem de erro
        code: Código do erro
        status_code: Código HTTP
        details: Detalhes adicionais
        request_id: ID da requisição para rastreamento
    
    Returns:
        Dicionário com resposta de erro formatada
    """
    error_response = {
        "error": {
            "message": message,
            "code": code,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return error_response


async def fluyte_exception_handler(request: Request, exc: FluyteException) -> JSONResponse:
    """Handler para exceções customizadas do Fluyt"""
    
    # Log do erro
    logger.error(
        f"FluyteException: {exc.code} - {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response = create_error_response(
        message=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=exc.details,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler para exceções HTTP padrão"""
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response = create_error_response(
        message=str(exc.detail),
        code="HTTP_ERROR",
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler para erros de validação do Pydantic"""
    
    # Extrai detalhes dos erros de validação
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation Error: {validation_errors}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": validation_errors
        }
    )
    
    response = create_error_response(
        message="Dados inválidos fornecidos",
        code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": validation_errors},
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para exceções gerais não tratadas"""
    
    # Log detalhado do erro
    logger.error(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # Em produção, não expor detalhes internos
    from core.config import settings
    
    if settings.is_production:
        message = "Erro interno do servidor"
        details = None
    else:
        message = f"Erro interno: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc().split('\n')
        }
    
    response = create_error_response(
        message=message,
        code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


def register_exception_handlers(app):
    """
    Registra todos os handlers de exceção na aplicação FastAPI.
    
    Args:
        app: Instância da aplicação FastAPI
    """
    app.add_exception_handler(FluyteException, fluyte_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 