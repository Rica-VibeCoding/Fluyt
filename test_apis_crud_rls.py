#!/usr/bin/env python3
"""
TESTE 3: CRUD OPERATIONS + RLS - VALIDAÇÃO DAS APIs FLUYT

Objetivo: Garantir que APIs funcionam corretamente com isolamento por loja

TESTES:
1. CRUD Clientes
2. CRUD Orçamentos  
3. RLS Isolamento
4. Validações de dados
5. Relacionamentos

Base URL: http://localhost:8000
"""

import requests
import json
import uuid
from datetime import datetime
import time

# Configurações
BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def print_test_header(title):
    """Imprimir cabeçalho do teste"""
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print(f"{'='*80}")

def print_result(endpoint, method, status_code, success, observation=""):
    """Imprimir resultado do teste"""
    status = "✅" if success else "❌"
    print(f"{status} {method} {endpoint} - Status {status_code} - {observation}")

def test_server_health():
    """Testar se servidor está respondendo"""
    print_test_header("TESTE 0: SERVER HEALTH")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_result("/health", "GET", response.status_code, True, "Servidor funcionando")
            return True
        else:
            print_result("/health", "GET", response.status_code, False, "Servidor com problema")
            return False
    except Exception as e:
        print_result("/health", "GET", "ERR", False, f"Erro de conexão: {e}")
        return False

def test_swagger_docs():
    """Testar se Swagger está acessível"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/docs", timeout=5)
        if response.status_code == 200:
            print_result("/api/v1/docs", "GET", response.status_code, True, "Swagger acessível")
            return True
        else:
            print_result("/api/v1/docs", "GET", response.status_code, False, "Swagger indisponível")
            return False
    except Exception as e:
        print_result("/api/v1/docs", "GET", "ERR", False, f"Erro: {e}")
        return False

def test_openapi_spec():
    """Testar se especificação OpenAPI está disponível"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/openapi.json", timeout=5)
        if response.status_code == 200:
            spec = response.json()
            endpoints = len(spec.get("paths", {}))
            print_result("/api/v1/openapi.json", "GET", response.status_code, True, f"{endpoints} endpoints documentados")
            return True
        else:
            print_result("/api/v1/openapi.json", "GET", response.status_code, False, "OpenAPI indisponível")
            return False
    except Exception as e:
        print_result("/api/v1/openapi.json", "GET", "ERR", False, f"Erro: {e}")
        return False

def mock_auth_headers(loja_id="test-loja-1", perfil="ADMIN_MASTER"):
    """Simular headers de autenticação para testes"""
    return {
        **HEADERS,
        "X-User-ID": str(uuid.uuid4()),
        "X-Loja-ID": loja_id,
        "X-User-Perfil": perfil,
        "X-User-Nome": "Teste Usuario"
    }

def test_crud_clientes():
    """Testar CRUD de clientes"""
    print_test_header("TESTE 1: CRUD CLIENTES")
    
    resultados = []
    
    # 1. Listar clientes existentes
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/clientes",
            headers=mock_auth_headers(),
            timeout=10
        )
        success = response.status_code == 200
        if success:
            clientes = response.json()
            print_result("/api/v1/clientes", "GET", response.status_code, True, f"{len(clientes)} clientes encontrados")
        else:
            print_result("/api/v1/clientes", "GET", response.status_code, False, "Erro ao listar clientes")
        resultados.append(success)
    except Exception as e:
        print_result("/api/v1/clientes", "GET", "ERR", False, f"Erro: {e}")
        resultados.append(False)
    
    # 2. Criar novo cliente
    novo_cliente = {
        "nome": f"Cliente Teste {datetime.now().strftime('%H%M%S')}",
        "cpf_cnpj": f"123.456.789-{datetime.now().strftime('%S')}",
        "telefone": "(11) 99999-9999",
        "email": f"teste{datetime.now().strftime('%H%M%S')}@fluyt.com",
        "endereco": "Rua Teste, 123",
        "cidade": "São Paulo",
        "cep": "01234-567",
        "tipo_venda": "NORMAL",
        "observacao": "Cliente criado via teste automatizado"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/clientes",
            headers=mock_auth_headers(),
            json=novo_cliente,
            timeout=10
        )
        success = response.status_code == 201
        if success:
            cliente_criado = response.json()
            cliente_id = cliente_criado.get("id")
            print_result("/api/v1/clientes", "POST", response.status_code, True, f"Cliente criado: {cliente_id}")
        else:
            print_result("/api/v1/clientes", "POST", response.status_code, False, f"Erro: {response.text}")
            cliente_id = None
        resultados.append(success)
    except Exception as e:
        print_result("/api/v1/clientes", "POST", "ERR", False, f"Erro: {e}")
        resultados.append(False)
        cliente_id = None
    
    # 3. Obter cliente específico (se criou com sucesso)
    if cliente_id:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/clientes/{cliente_id}",
                headers=mock_auth_headers(),
                timeout=10
            )
            success = response.status_code == 200
            if success:
                cliente = response.json()
                print_result(f"/api/v1/clientes/{cliente_id}", "GET", response.status_code, True, f"Cliente obtido: {cliente.get('nome')}")
            else:
                print_result(f"/api/v1/clientes/{cliente_id}", "GET", response.status_code, False, "Erro ao obter cliente")
            resultados.append(success)
        except Exception as e:
            print_result(f"/api/v1/clientes/{cliente_id}", "GET", "ERR", False, f"Erro: {e}")
            resultados.append(False)
        
        # 4. Atualizar cliente
        dados_atualizacao = {
            "nome": f"Cliente Atualizado {datetime.now().strftime('%H%M%S')}",
            "telefone": "(11) 88888-8888"
        }
        
        try:
            response = requests.put(
                f"{BASE_URL}/api/v1/clientes/{cliente_id}",
                headers=mock_auth_headers(),
                json=dados_atualizacao,
                timeout=10
            )
            success = response.status_code == 200
            if success:
                print_result(f"/api/v1/clientes/{cliente_id}", "PUT", response.status_code, True, "Cliente atualizado")
            else:
                print_result(f"/api/v1/clientes/{cliente_id}", "PUT", response.status_code, False, f"Erro: {response.text}")
            resultados.append(success)
        except Exception as e:
            print_result(f"/api/v1/clientes/{cliente_id}", "PUT", "ERR", False, f"Erro: {e}")
            resultados.append(False)
    
    print(f"\n🎯 RESULTADO CRUD CLIENTES: {sum(resultados)}/{len(resultados)} testes passaram")
    return resultados

def test_crud_orcamentos():
    """Testar CRUD de orçamentos"""
    print_test_header("TESTE 2: CRUD ORÇAMENTOS")
    
    resultados = []
    
    # 1. Listar orçamentos existentes
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/orcamentos",
            headers=mock_auth_headers(),
            timeout=10
        )
        success = response.status_code == 200
        if success:
            orcamentos = response.json()
            print_result("/api/v1/orcamentos", "GET", response.status_code, True, f"{len(orcamentos)} orçamentos encontrados")
        else:
            print_result("/api/v1/orcamentos", "GET", response.status_code, False, "Erro ao listar orçamentos")
        resultados.append(success)
    except Exception as e:
        print_result("/api/v1/orcamentos", "GET", "ERR", False, f"Erro: {e}")
        resultados.append(False)
    
    # 2. Buscar dados necessários para criar orçamento
    # TODO: Implementar busca de cliente_id, ambiente_ids, etc. quando endpoints estiverem disponíveis
    
    print(f"\n🎯 RESULTADO CRUD ORÇAMENTOS: {sum(resultados)}/{len(resultados)} testes passaram")
    return resultados

def test_rls_isolamento():
    """Testar isolamento RLS entre lojas"""
    print_test_header("TESTE 3: RLS ISOLAMENTO")
    
    resultados = []
    
    # Testar com duas lojas diferentes
    loja_a_headers = mock_auth_headers(loja_id="loja-a")
    loja_b_headers = mock_auth_headers(loja_id="loja-b")
    
    # 1. Criar cliente na loja A
    cliente_loja_a = {
        "nome": "Cliente Loja A",
        "cpf_cnpj": "111.111.111-11",
        "telefone": "(11) 11111-1111",
        "email": "loja_a@teste.com",
        "endereco": "Endereço A",
        "cidade": "Cidade A",
        "cep": "11111-111",
        "tipo_venda": "NORMAL"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/clientes",
            headers=loja_a_headers,
            json=cliente_loja_a,
            timeout=10
        )
        if response.status_code == 201:
            cliente_a_id = response.json().get("id")
            print_result("/api/v1/clientes (Loja A)", "POST", response.status_code, True, f"Cliente criado na loja A: {cliente_a_id}")
            
            # 2. Tentar acessar cliente da loja A usando credenciais da loja B
            try:
                response_b = requests.get(
                    f"{BASE_URL}/api/v1/clientes/{cliente_a_id}",
                    headers=loja_b_headers,
                    timeout=10
                )
                # Deve retornar 404 ou 403 (RLS bloqueando)
                success = response_b.status_code in [403, 404]
                if success:
                    print_result(f"/api/v1/clientes/{cliente_a_id} (Loja B)", "GET", response_b.status_code, True, "RLS funcionando - acesso negado")
                else:
                    print_result(f"/api/v1/clientes/{cliente_a_id} (Loja B)", "GET", response_b.status_code, False, "RLS FALHOU - acesso permitido indevidamente")
                resultados.append(success)
            except Exception as e:
                print_result(f"/api/v1/clientes/{cliente_a_id} (Loja B)", "GET", "ERR", False, f"Erro: {e}")
                resultados.append(False)
        else:
            print_result("/api/v1/clientes (Loja A)", "POST", response.status_code, False, "Falha ao criar cliente loja A")
            resultados.append(False)
    except Exception as e:
        print_result("/api/v1/clientes (Loja A)", "POST", "ERR", False, f"Erro: {e}")
        resultados.append(False)
    
    print(f"\n🎯 RESULTADO RLS ISOLAMENTO: {sum(resultados)}/{len(resultados)} testes passaram")
    return resultados

def test_validacoes():
    """Testar validações de dados"""
    print_test_header("TESTE 4: VALIDAÇÕES DE DADOS")
    
    resultados = []
    
    # 1. Criar cliente sem nome (deve falhar)
    cliente_invalido = {
        "cpf_cnpj": "123.456.789-00",
        "telefone": "(11) 99999-9999"
        # nome ausente - deve gerar erro 422
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/clientes",
            headers=mock_auth_headers(),
            json=cliente_invalido,
            timeout=10
        )
        # Deve retornar 422 (Validation Error)
        success = response.status_code == 422
        if success:
            print_result("/api/v1/clientes (sem nome)", "POST", response.status_code, True, "Validação funcionando - nome obrigatório")
        else:
            print_result("/api/v1/clientes (sem nome)", "POST", response.status_code, False, "Validação FALHOU - aceito dados inválidos")
        resultados.append(success)
    except Exception as e:
        print_result("/api/v1/clientes (sem nome)", "POST", "ERR", False, f"Erro: {e}")
        resultados.append(False)
    
    # 2. Criar cliente com email inválido
    cliente_email_invalido = {
        "nome": "Cliente Teste",
        "cpf_cnpj": "123.456.789-00",
        "email": "email_invalido_sem_arroba",
        "telefone": "(11) 99999-9999",
        "endereco": "Rua Teste",
        "cidade": "Cidade",
        "cep": "12345-678",
        "tipo_venda": "NORMAL"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/clientes",
            headers=mock_auth_headers(),
            json=cliente_email_invalido,
            timeout=10
        )
        # Deve retornar 422 se houver validação de email
        success = response.status_code in [422, 400]
        if success:
            print_result("/api/v1/clientes (email inválido)", "POST", response.status_code, True, "Validação email funcionando")
        else:
            print_result("/api/v1/clientes (email inválido)", "POST", response.status_code, False, "Validação email não implementada")
        resultados.append(success)
    except Exception as e:
        print_result("/api/v1/clientes (email inválido)", "POST", "ERR", False, f"Erro: {e}")
        resultados.append(False)
    
    print(f"\n🎯 RESULTADO VALIDAÇÕES: {sum(resultados)}/{len(resultados)} testes passaram")
    return resultados

def test_endpoints_disponiveis():
    """Listar endpoints disponíveis"""
    print_test_header("TESTE 5: ENDPOINTS DISPONÍVEIS")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/openapi.json", timeout=10)
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get("paths", {})
            
            print(f"\n📋 ENDPOINTS DISPONÍVEIS ({len(paths)} total):")
            for path, methods in paths.items():
                for method in methods.keys():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        print(f"   {method.upper()} {path}")
            
            return True
        else:
            print("❌ Não foi possível obter especificação da API")
            return False
    except Exception as e:
        print(f"❌ Erro ao obter endpoints: {e}")
        return False

def main():
    """Executar todos os testes"""
    print("🚀 TESTE 3: CRUD OPERATIONS + RLS - VALIDAÇÃO APIS FLUYT")
    print("🎯 Objetivo: Garantir que APIs funcionam corretamente com isolamento por loja")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📅 Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Aguardar servidor inicializar
    print("\n⏳ Aguardando servidor inicializar...")
    time.sleep(3)
    
    todos_resultados = []
    
    # 0. Testar saúde do servidor
    if not test_server_health():
        print("\n❌ SERVIDOR NÃO ESTÁ FUNCIONANDO - ABORTAR TESTES")
        return False
    
    # Swagger
    test_swagger_docs()
    test_openapi_spec()
    
    # Endpoints disponíveis
    test_endpoints_disponiveis()
    
    # 1. CRUD Clientes
    resultados_clientes = test_crud_clientes()
    todos_resultados.extend(resultados_clientes)
    
    # 2. CRUD Orçamentos
    resultados_orcamentos = test_crud_orcamentos()
    todos_resultados.extend(resultados_orcamentos)
    
    # 3. RLS Isolamento
    resultados_rls = test_rls_isolamento()
    todos_resultados.extend(resultados_rls)
    
    # 4. Validações
    resultados_validacoes = test_validacoes()
    todos_resultados.extend(resultados_validacoes)
    
    # Resumo final
    print(f"\n{'='*80}")
    print("📊 RESUMO FINAL DOS TESTES")
    print(f"{'='*80}")
    
    total_testes = len(todos_resultados)
    testes_passaram = sum(todos_resultados)
    percentual = (testes_passaram / total_testes * 100) if total_testes > 0 else 0
    
    print(f"🎯 RESULTADO GERAL: {testes_passaram}/{total_testes} testes passaram ({percentual:.1f}%)")
    
    if percentual >= 80:
        print("✅ APIS FUNCIONANDO - Frontend pode ser desenvolvido")
    elif percentual >= 50:
        print("⚠️ APIS PARCIALMENTE FUNCIONANDO - Verificar problemas")
    else:
        print("❌ APIS COM PROBLEMAS CRÍTICOS - Corrigir antes do frontend")
    
    print(f"{'='*80}")
    
    return percentual >= 80

if __name__ == "__main__":
    main() 