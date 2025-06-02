"""
Módulo de endpoints temporários para teste sem autenticação.

⚠️ ATENÇÃO: Este módulo deve ser REMOVIDO após validação completa!
Endpoints sem segurança apenas para testes de desenvolvimento.
"""

from .routes import router

__all__ = ["router"] 