#!/usr/bin/env python3
"""
Script de teste para validar importações e configurações básicas do Fluyt Backend
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_basic_imports():
    """Testa importações básicas do Python"""
    print("🔍 TESTE 1: Importações básicas do Python")
    
    try:
        import json
        import datetime
        import uuid
        print("✅ Importações básicas - OK")
        return True
    except Exception as e:
        print(f"❌ Erro em importações básicas: {e}")
        return False

def test_external_dependencies():
    """Testa dependências externas principais"""
    print("\n🔍 TESTE 2: Dependências externas")
    
    dependencies = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'supabase',
        'pandas',
        'loguru'
    ]
    
    results = {}
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - Disponível")
            results[dep] = True
        except ImportError:
            print(f"❌ {dep} - NÃO ENCONTRADO")
            results[dep] = False
        except Exception as e:
            print(f"⚠️ {dep} - Erro: {e}")
            results[dep] = False
    
    return results

def test_core_modules():
    """Testa módulos core do projeto"""
    print("\n🔍 TESTE 3: Módulos core do projeto")
    
    try:
        from core.config import get_settings
        settings = get_settings()
        print(f"✅ Config carregada - Ambiente: {settings.environment}")
        
        from core.database import SupabaseClient
        print("✅ Database module - OK")
        
        from core.auth import AuthMiddleware
        print("✅ Auth module - OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro em módulos core: {e}")
        return False

def test_business_modules():
    """Testa módulos de negócio"""
    print("\n🔍 TESTE 4: Módulos de negócio")
    
    modules = [
        'modules.clientes.services',
        'modules.orcamentos.services',
        'modules.clientes.controller',
        'modules.orcamentos.controller'
    ]
    
    results = {}
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
            results[module] = True
        except Exception as e:
            print(f"❌ {module} - Erro: {e}")
            results[module] = False
    
    return results

def test_fastapi_app():
    """Testa criação da aplicação FastAPI"""
    print("\n🔍 TESTE 5: Criação da aplicação FastAPI")
    
    try:
        from main import app
        print(f"✅ App FastAPI criada: {app.title}")
        
        # Testa endpoints básicos
        routes = [route.path for route in app.routes]
        print(f"✅ {len(routes)} rotas carregadas")
        
        if "/health" in routes:
            print("✅ Health check endpoint - OK")
        else:
            print("⚠️ Health check endpoint - NÃO ENCONTRADO")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar app FastAPI: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DE VALIDAÇÃO - FLUYT BACKEND\n")
    
    results = {}
    
    # Teste 1: Importações básicas
    results['basic_imports'] = test_basic_imports()
    
    # Teste 2: Dependências externas  
    results['dependencies'] = test_external_dependencies()
    
    # Teste 3: Módulos core
    results['core_modules'] = test_core_modules()
    
    # Teste 4: Módulos de negócio
    results['business_modules'] = test_business_modules()
    
    # Teste 5: App FastAPI
    results['fastapi_app'] = test_fastapi_app()
    
    # Resumo final
    print(f"\n📊 RESUMO DOS TESTES:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test}")
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Backend pronto para execução.")
    else:
        print("⚠️ Alguns testes falharam. Verifique dependências e configurações.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 