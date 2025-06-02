"""
Rotas temporárias para testes SEM AUTENTICAÇÃO.

⚠️ REMOVER APÓS VALIDAÇÃO COMPLETA!
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from decimal import Decimal

from .schemas import (
    TestClienteCreate,
    TestAmbienteCreate, 
    TestOrcamentoCreate,
    TestCalculoEngine,
    TestResponse,
    TestRLSValidation
)
from .service import TestService
from .mock_service import MockTestService

router = APIRouter(prefix="/test", tags=["🚨 TESTE TEMPORÁRIO"])

def get_test_service():
    """Retorna uma instância do TestService ou MockTestService se Supabase não estiver disponível"""
    try:
        service = TestService()
        # Testar se consegue acessar o Supabase
        _ = service.supabase
        return service
    except ValueError:
        # Supabase não configurado, usar mock
        return MockTestService()

@router.get("/")
async def info_testes():
    """Informações sobre os endpoints de teste"""
    return {
        "aviso": "⚠️ ENDPOINTS TEMPORÁRIOS SEM AUTENTICAÇÃO",
        "objetivo": "Testar funcionalidades completas do sistema",
        "remover_apos": "Validação completa",
        "endpoints_disponiveis": [
            "GET /test/dados-iniciais - Buscar lojas, equipe, configs",
            "POST /test/cliente - Criar cliente",
            "GET /test/clientes - Listar clientes por loja",
            "POST /test/ambiente - Criar ambiente",
            "POST /test/orcamento - Criar orçamento completo",
            "GET /test/orcamentos - Listar orçamentos por loja",
            "POST /test/calculo - Testar engine isoladamente",
            "POST /test/rls - Testar isolamento RLS",
            "POST /test/validacoes - Testar validações Pydantic"
        ]
    }

@router.get("/dados-iniciais", response_model=TestResponse)
async def buscar_dados_iniciais():
    """Buscar dados iniciais necessários para testes"""
    test_service = get_test_service()
    return await test_service.buscar_dados_iniciais()

@router.post("/cliente", response_model=TestResponse)
async def criar_cliente_teste(dados: TestClienteCreate):
    """Criar cliente para teste - SEM JWT"""
    test_service = get_test_service()
    return await test_service.criar_cliente_teste(dados)

@router.get("/clientes", response_model=TestResponse)
async def listar_clientes_teste(loja_id: str = Query(..., description="ID da loja")):
    """Listar clientes por loja - Teste RLS"""
    test_service = get_test_service()
    return await test_service.listar_clientes_teste(loja_id)

@router.post("/ambiente", response_model=TestResponse)
async def criar_ambiente_teste(dados: TestAmbienteCreate):
    """Criar ambiente para teste"""
    test_service = get_test_service()
    return await test_service.criar_ambiente_teste(dados)

@router.post("/orcamento", response_model=TestResponse)
async def criar_orcamento_teste(dados: TestOrcamentoCreate):
    """Criar orçamento completo com cálculos automáticos"""
    test_service = get_test_service()
    return await test_service.criar_orcamento_teste(dados)

@router.get("/orcamentos", response_model=TestResponse)
async def listar_orcamentos_teste(loja_id: str = Query(..., description="ID da loja")):
    """Listar orçamentos por loja - Teste RLS"""
    test_service = get_test_service()
    return await test_service.listar_orcamentos_teste(loja_id)

@router.post("/calculo", response_model=TestResponse)
async def testar_calculo_engine(dados: TestCalculoEngine):
    """Testar engine de cálculo isoladamente"""
    test_service = get_test_service()
    return await test_service.calcular_custos_engine(
        valor_ambientes=dados.valor_ambientes,
        desconto_percentual=dados.desconto_percentual,
        loja_id=dados.loja_id,
        vendedor_id=dados.vendedor_id,
        custos_adicionais=dados.custos_adicionais or []
    )

@router.post("/rls", response_model=TestResponse)  
async def testar_rls_isolamento(dados: TestRLSValidation):
    """Testar isolamento RLS entre lojas"""
    test_service = get_test_service()
    return await test_service.testar_rls_isolamento(
        loja_origem=dados.loja_origem,
        loja_destino=dados.loja_destino
    )

@router.post("/validacoes")
async def testar_validacoes_pydantic():
    """Testar validações Pydantic com dados inválidos"""
    try:
        # Teste 1: Cliente com dados inválidos
        test_service = get_test_service()
        try:
            TestClienteCreate(
                nome="",  # Inválido - vazio
                cpf_cnpj="123",  # Inválido - muito curto
                telefone="abc",  # Inválido - não numérico
                endereco="",  # Inválido - vazio
                cidade="",  # Inválido - vazio
                cep="123",  # Inválido - muito curto
                loja_id=""  # Inválido - vazio
            )
        except Exception as e:
            teste1_erro = str(e)
        else:
            teste1_erro = "FALHOU - Deveria ter dado erro!"

        # Teste 2: Orçamento com valores negativos
        try:
            TestCalculoEngine(
                valor_ambientes=Decimal('-1000'),  # Inválido - negativo
                desconto_percentual=Decimal('150'),  # Inválido - > 100%
                loja_id="",  # Inválido - vazio
                vendedor_id=""  # Inválido - vazio
            )
        except Exception as e:
            teste2_erro = str(e)
        else:
            teste2_erro = "FALHOU - Deveria ter dado erro!"

        return TestResponse(
            success=True,
            message="Validações Pydantic testadas",
            data={
                "teste_cliente_invalido": teste1_erro,
                "teste_calculo_invalido": teste2_erro,
                "conclusao": "Validações funcionando se houve erros acima"
            }
        )

    except Exception as e:
        return TestResponse(
            success=False,
            message="Erro ao testar validações",
            errors=[str(e)]
        )

# Endpoints especiais para testes específicos

@router.post("/cenario-completo")
async def executar_cenario_completo_teste():
    """
    Executa um cenário completo de teste:
    1. Busca dados iniciais
    2. Cria cliente
    3. Cria ambientes  
    4. Cria orçamento
    5. Valida cálculos
    """
    try:
        resultados = []
        
        # 1. Buscar dados iniciais
        test_service = get_test_service()
        dados_iniciais = await test_service.buscar_dados_iniciais()
        resultados.append({"etapa": "dados_iniciais", "resultado": dados_iniciais})
        
        if not dados_iniciais.success or not dados_iniciais.data['lojas']:
            return TestResponse(
                success=False,
                message="Falha ao buscar dados iniciais",
                data={"resultados": resultados}
            )
        
        loja_id = dados_iniciais.data['lojas'][0]['id']
        vendedor_id = dados_iniciais.data['equipe'][0]['id'] if dados_iniciais.data['equipe'] else None
        
        if not vendedor_id:
            return TestResponse(
                success=False,
                message="Nenhum vendedor encontrado para teste",
                data={"resultados": resultados}
            )
        
        # 2. Criar cliente
        test_service = get_test_service()
        cliente_dados = TestClienteCreate(
            nome="Cliente Teste Completo",
            cpf_cnpj="12345678901",
            telefone="11999999999",
            email="teste@email.com",
            endereco="Rua Teste, 123",
            cidade="São Paulo",
            cep="01234567",
            loja_id=loja_id,
            tipo_venda="NORMAL"
        )
        
        cliente_resultado = await test_service.criar_cliente_teste(cliente_dados)
        resultados.append({"etapa": "criar_cliente", "resultado": cliente_resultado})
        
        if not cliente_resultado.success:
            return TestResponse(
                success=False,
                message="Falha ao criar cliente",
                data={"resultados": resultados}
            )
        
        cliente_id = cliente_resultado.data['cliente']['id']
        
        # 3. Criar ambientes
        test_service = get_test_service()
        ambiente1_dados = TestAmbienteCreate(
            nome_ambiente="Cozinha Teste",
            nome_cliente="Cliente Teste",
            valor_total=Decimal('25000'),
            linha_produto="Unique",
            descricao_completa="Cozinha completa teste",
            loja_id=loja_id
        )
        
        ambiente1_resultado = await test_service.criar_ambiente_teste(ambiente1_dados)
        resultados.append({"etapa": "criar_ambiente1", "resultado": ambiente1_resultado})
        
        ambiente2_dados = TestAmbienteCreate(
            nome_ambiente="Dormitório Teste",
            nome_cliente="Cliente Teste",
            valor_total=Decimal('15000'),
            linha_produto="Sublime",
            descricao_completa="Dormitório completo teste",
            loja_id=loja_id
        )
        
        ambiente2_resultado = await test_service.criar_ambiente_teste(ambiente2_dados)
        resultados.append({"etapa": "criar_ambiente2", "resultado": ambiente2_resultado})
        
        if not ambiente1_resultado.success or not ambiente2_resultado.success:
            return TestResponse(
                success=False,
                message="Falha ao criar ambientes",
                data={"resultados": resultados}
            )
        
        ambientes_ids = [
            ambiente1_resultado.data['ambiente']['id'],
            ambiente2_resultado.data['ambiente']['id']
        ]
        
        # 4. Criar orçamento
        test_service = get_test_service()
        orcamento_dados = TestOrcamentoCreate(
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            loja_id=loja_id,
            ambientes_ids=ambientes_ids,
            desconto_percentual=Decimal('10'),
            custos_adicionais=[
                {"descricao": "Taxa projeto especial", "valor": 500},
                {"descricao": "Comissão indicador", "valor": 300}
            ]
        )
        
        orcamento_resultado = await test_service.criar_orcamento_teste(orcamento_dados)
        resultados.append({"etapa": "criar_orcamento", "resultado": orcamento_resultado})
        
        # 5. Validar cálculo específico R$ 40.000 → R$ 2.400
        test_service = get_test_service()
        calculo_teste_dados = TestCalculoEngine(
            valor_ambientes=Decimal('40000'),
            desconto_percentual=Decimal('0'),
            loja_id=loja_id,
            vendedor_id=vendedor_id,
            custos_adicionais=[]
        )
        
        calculo_teste_resultado = await test_service.calcular_custos_engine(
            valor_ambientes=calculo_teste_dados.valor_ambientes,
            desconto_percentual=calculo_teste_dados.desconto_percentual,
            loja_id=calculo_teste_dados.loja_id,
            vendedor_id=calculo_teste_dados.vendedor_id,
            custos_adicionais=calculo_teste_dados.custos_adicionais
        )
        resultados.append({"etapa": "teste_calculo_40k", "resultado": calculo_teste_resultado})
        
        # Verificar se comissão está correta (deve ser R$ 2.400)
        comissao_esperada = 2400.0
        comissao_calculada = calculo_teste_resultado.data['custos']['comissao_vendedor'] if calculo_teste_resultado.success else 0
        calculo_correto = abs(comissao_calculada - comissao_esperada) < 0.01
        
        return TestResponse(
            success=True,
            message="Cenário completo executado",
            data={
                "resultados": resultados,
                "validacao_calculo": {
                    "valor_testado": 40000,
                    "comissao_esperada": comissao_esperada,
                    "comissao_calculada": comissao_calculada,
                    "calculo_correto": calculo_correto
                },
                "resumo": {
                    "etapas_executadas": len(resultados),
                    "sucessos": sum(1 for r in resultados if r["resultado"].success),
                    "falhas": sum(1 for r in resultados if not r["resultado"].success)
                }
            }
        )
        
    except Exception as e:
        return TestResponse(
            success=False,
            message="Erro no cenário completo",
            errors=[str(e)]
        ) 