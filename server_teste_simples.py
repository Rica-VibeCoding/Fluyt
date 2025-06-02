#!/usr/bin/env python3
"""
Servidor de Teste Simplificado - Fluyt Comercial

Servidor mínimo apenas para executar os testes de endpoints.
Usa dados mock, não depende do Supabase.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.modules.test_endpoints.routes import router as test_router

# Criar aplicação FastAPI mínima
app = FastAPI(
    title="Fluyt Test Server",
    description="Servidor de teste temporário com dados mock",
    version="1.0.0"
)

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "server": "test-mock"}

# Registrar apenas as rotas de teste
app.include_router(test_router, prefix="/api/v1")

if __name__ == "__main__":
    print("🚀 Iniciando Servidor de Teste com Dados Mock")
    print("📍 URL: http://localhost:8000")
    print("📋 Documentação: http://localhost:8000/docs")
    print("⚠️  Este servidor usa apenas dados simulados!")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    ) 