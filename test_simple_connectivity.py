#!/usr/bin/env python3
"""
TESTE SIMPLES: CONECTIVIDADE E ESTRUTURA DAS APIs

Foco: Verificar se APIs estão estruturadas corretamente e servidor está funcionando
Não testa autenticação complexa, apenas estrutura e documentação
"""

import requests
import json
from datetime import datetime
import sys

# Configurações
BASE_URL = "http://localhost:8000"

def test_basic_connectivity():
    """Teste básico de conectividade"""
    print("🔍 TESTE 1: CONECTIVIDADE BÁSICA")
    print("-" * 50)
    
    tests = [
        ("Health Check", "GET", "/health"),
        ("Root Endpoint", "GET", "/"),
        ("OpenAPI Spec", "GET", "/api/v1/openapi.json"),
        ("Swagger UI", "GET", "/api/v1/docs"),
        ("Redoc", "GET", "/api/v1/redoc")
    ]
    
    results = []
    
    for name, method, endpoint in tests:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            success = response.status_code == 200
            status = "✅" if success else "❌"
            print(f"{status} {name}: {method} {endpoint} - Status {response.status_code}")
            results.append(success)
        except Exception as e:
            print(f"❌ {name}: {method} {endpoint} - ERRO: {e}")
            results.append(False)
    
    return results

def test_api_structure():
    """Teste da estrutura das APIs"""
    print(f"\n🏗️ TESTE 2: ESTRUTURA DAS APIs")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/openapi.json", timeout=10)
        if response.status_code != 200:
            print("❌ Não foi possível obter especificação OpenAPI")
            return False
        
        spec = response.json()
        paths = spec.get("paths", {})
        
        # Contadores por módulo
        modulos = {}
        for path in paths.keys():
            if "/api/v1/" in path:
                # Extrair módulo da URL
                parts = path.split("/")
                if len(parts) >= 4:  # ['', 'api', 'v1', 'modulo', ...]
                    modulo = parts[3]
                    if modulo not in modulos:
                        modulos[modulo] = 0
                    modulos[modulo] += 1
        
        print(f"📊 ENDPOINTS POR MÓDULO ({len(paths)} total):")
        for modulo, count in sorted(modulos.items()):
            print(f"   📁 {modulo}: {count} endpoints")
        
        # Verificar módulos esperados
        modulos_esperados = [
            "clientes", "orcamentos", "ambientes", "auth", 
            "contratos", "aprovacoes", "configuracoes"
        ]
        
        modulos_encontrados = set(modulos.keys())
        modulos_faltando = set(modulos_esperados) - modulos_encontrados
        
        if modulos_faltando:
            print(f"\n⚠️ MÓDULOS FALTANDO: {', '.join(modulos_faltando)}")
        else:
            print(f"\n✅ TODOS OS MÓDULOS PRINCIPAIS ENCONTRADOS")
        
        return len(modulos_faltando) == 0
        
    except Exception as e:
        print(f"❌ Erro ao analisar estrutura: {e}")
        return False

def test_public_endpoints():
    """Teste endpoints que deveriam ser públicos"""
    print(f"\n🌐 TESTE 3: ENDPOINTS PÚBLICOS")
    print("-" * 50)
    
    # Endpoints que talvez sejam públicos ou tenham menos restrições
    public_tests = [
        ("Health", "GET", "/health"),
        ("Root", "GET", "/"),
    ]
    
    results = []
    
    for name, method, endpoint in public_tests:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            success = response.status_code == 200
            status = "✅" if success else "❌"
            
            if success and endpoint == "/health":
                # Verificar conteúdo da resposta de health
                try:
                    data = response.json()
                    print(f"{status} {name}: {data}")
                except:
                    print(f"{status} {name}: Response OK (não-JSON)")
            else:
                print(f"{status} {name}: Status {response.status_code}")
            
            results.append(success)
        except Exception as e:
            print(f"❌ {name}: ERRO: {e}")
            results.append(False)
    
    return results

def test_protected_endpoints_structure():
    """Teste se endpoints protegidos retornam erro 401/403 adequadamente"""
    print(f"\n🔒 TESTE 4: ESTRUTURA DE AUTENTICAÇÃO")
    print("-" * 50)
    
    # Endpoints que devem estar protegidos
    protected_tests = [
        ("Listar Clientes", "GET", "/api/v1/clientes/"),
        ("Listar Orçamentos", "GET", "/api/v1/orcamentos/"),
        ("Buscar Equipe", "GET", "/api/v1/auth/equipe/"),
    ]
    
    results = []
    
    for name, method, endpoint in protected_tests:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            # Esperamos 401 (Unauthorized) ou 403 (Forbidden)
            expected_status = response.status_code in [401, 403]
            status = "✅" if expected_status else "❌"
            
            if expected_status:
                print(f"{status} {name}: Protegido adequadamente (Status {response.status_code})")
            else:
                print(f"{status} {name}: Status inesperado {response.status_code}")
            
            results.append(expected_status)
        except Exception as e:
            print(f"❌ {name}: ERRO: {e}")
            results.append(False)
    
    return results

def main():
    """Executar todos os testes simples"""
    print("🚀 TESTE SIMPLES: CONECTIVIDADE E ESTRUTURA DAS APIs FLUYT")
    print("=" * 70)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📅 Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Verificar estrutura básica sem autenticação complexa")
    
    todos_resultados = []
    
    # 1. Conectividade básica
    resultados_conn = test_basic_connectivity()
    todos_resultados.extend(resultados_conn)
    
    # 2. Estrutura das APIs
    resultado_estrutura = test_api_structure()
    todos_resultados.append(resultado_estrutura)
    
    # 3. Endpoints públicos
    resultados_public = test_public_endpoints()
    todos_resultados.extend(resultados_public)
    
    # 4. Estrutura de autenticação
    resultados_auth = test_protected_endpoints_structure()
    todos_resultados.extend(resultados_auth)
    
    # Resumo final
    print(f"\n{'='*70}")
    print("📊 RESUMO FINAL")
    print(f"{'='*70}")
    
    total_testes = len(todos_resultados)
    testes_passaram = sum(todos_resultados)
    percentual = (testes_passaram / total_testes * 100) if total_testes > 0 else 0
    
    print(f"🎯 RESULTADO: {testes_passaram}/{total_testes} testes passaram ({percentual:.1f}%)")
    
    if percentual >= 90:
        status_final = "✅ ESTRUTURA EXCELENTE - Backend funcionando perfeitamente"
    elif percentual >= 75:
        status_final = "✅ ESTRUTURA BOA - Backend funcionando bem"
    elif percentual >= 50:
        status_final = "⚠️ ESTRUTURA PARCIAL - Alguns problemas detectados"
    else:
        status_final = "❌ ESTRUTURA COM PROBLEMAS - Verificar configurações"
    
    print(f"\n{status_final}")
    
    print(f"\n💡 PRÓXIMOS PASSOS:")
    print(f"   1. ✅ Conectividade: {'OK' if resultados_conn else 'VERIFICAR'}")
    print(f"   2. ✅ Estrutura APIs: {'OK' if resultado_estrutura else 'VERIFICAR'}")
    print(f"   3. ✅ Autenticação: {'CONFIGURADA' if any(resultados_auth) else 'VERIFICAR'}")
    print(f"   4. 🔄 Próximo: Configurar JWT para testes completos")
    
    print(f"{'='*70}")
    
    return percentual >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 