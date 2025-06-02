"""
Configurações centrais do sistema Fluyt Comercial.
Utiliza Pydantic Settings para validação de tipos e carregamento de variáveis de ambiente.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional, Union
import os


class Settings(BaseSettings):
    """Configurações principais da aplicação"""
    
    # ===== APLICAÇÃO =====
    app_name: str = "Fluyt Comercial API"
    api_version: str = Field(default="v1", env="API_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ===== SUPABASE =====
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(default="", env="SUPABASE_SERVICE_KEY")
    
    # ===== JWT =====
    jwt_secret_key: str = Field(default="development-secret-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # ===== CORS =====
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="CORS_ORIGINS"
    )
    
    # ===== FILE UPLOAD =====
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    allowed_file_extensions: str = Field(default=".xml", env="ALLOWED_FILE_EXTENSIONS")
    
    # ===== DATABASE =====
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=0, env="DB_MAX_OVERFLOW")
    
    @field_validator('cors_origins')
    @classmethod
    def parse_cors_origins(cls, v):
        """Converte string separada por vírgula em lista"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('allowed_file_extensions')
    @classmethod
    def parse_file_extensions(cls, v):
        """Converte string separada por vírgula em lista"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',') if ext.strip()]
        return v
    
    @field_validator('supabase_url')
    @classmethod
    def validate_supabase_url(cls, v):
        """Valida se a URL do Supabase está correta (apenas em produção)"""
        # Em desenvolvimento, permite URL vazia
        if not v:
            return v
        if not v.startswith('https://'):
            raise ValueError('SUPABASE_URL deve começar com https://')
        return v
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em ambiente de desenvolvimento"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção"""
        return self.environment.lower() == "production"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Retorna o tamanho máximo de arquivo em bytes"""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna CORS origins como lista"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
        return self.cors_origins

    @property
    def allowed_file_extensions_list(self) -> List[str]:
        """Retorna extensões permitidas como lista"""
        if isinstance(self.allowed_file_extensions, str):
            return [ext.strip() for ext in self.allowed_file_extensions.split(',') if ext.strip()]
        return self.allowed_file_extensions

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignora variáveis extras do .env
    }


# Instância global das configurações
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection para FastAPI.
    Retorna a instância das configurações.
    """
    return settings
