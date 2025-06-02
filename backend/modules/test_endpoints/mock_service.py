"""
Service mock para testes sem Supabase.
Simula dados para validar funcionalidades.
"""

import uuid
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime

from .schemas import (
    TestClienteCreate, 
    TestAmbienteCreate, 
    TestOrcamentoCreate, 
    TestCalculoEngine,
    TestResponse
)

class MockTestService:
    def __init__(self):
        # Dados simulados
        self.mock_lojas = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "nome": "D-Art Móveis",
                "endereco": "Rua das Flores, 123",
                "telefone": "(11) 1234-5678",
                "email": "contato@dart.com.br",
                "ativo": True
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002", 
                "nome": "Romanza Móveis",
                "endereco": "Av. Principal, 456",
                "telefone": "(11) 8765-4321",
                "email": "contato@romanza.com.br",
                "ativo": True
            }
        ]
        
        self.mock_equipe = [
            {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "nome": "João Vendedor",
                "email": "joao@dart.com.br",
                "perfil": "VENDEDOR",
                "loja_id": "550e8400-e29b-41d4-a716-446655440001",
                "limite_desconto": 15.0,
                "ativo": True
            },
            {
                "id": "660e8400-e29b-41d4-a716-446655440002",
                "nome": "Maria Gerente",
                "email": "maria@dart.com.br", 
                "perfil": "GERENTE",
                "loja_id": "550e8400-e29b-41d4-a716-446655440001",
                "limite_desconto": 25.0,
                "ativo": True
            }
        ]
        
        self.mock_configs = [
            {
                "id": "770e8400-e29b-41d4-a716-446655440001",
                "loja_id": "550e8400-e29b-41d4-a716-446655440001",
                "deflator_custo_fabrica": 0.40,
                "valor_medidor_padrao": 200.0,
                "valor_frete_percentual": 0.02,
                "limite_desconto_vendedor": 0.15,
                "limite_desconto_gerente": 0.25,
                "proximo_numero_orcamento": 1,
                "prefixo_numeracao": "D-"
            }
        ]
        
        # Faixas de comissão mock
        self.mock_comissao_regras = [
            {
                "loja_id": "550e8400-e29b-41d4-a716-446655440001",
                "tipo_comissao": "VENDEDOR",
                "valor_minimo": 0,
                "valor_maximo": 25000,
                "percentual": 0.05,  # 5%
                "ordem": 1
            },
            {
                "loja_id": "550e8400-e29b-41d4-a716-446655440001",
                "tipo_comissao": "VENDEDOR", 
                "valor_minimo": 25000.01,
                "valor_maximo": 50000,
                "percentual": 0.06,  # 6%
                "ordem": 2
            },
            {
                "loja_id": "550e8400-e29b-41d4-a716-446655440001",
                "tipo_comissao": "VENDEDOR",
                "valor_minimo": 50000.01,
                "valor_maximo": None,  # Infinito
                "percentual": 0.08,  # 8%
                "ordem": 3
            }
        ]
        
        # Dados criados durante testes
        self.created_clientes = []
        self.created_ambientes = []
        self.created_orcamentos = []

    def calcular_comissao_faixa_unica(self, valor_venda: Decimal, loja_id: str, vendedor_id: str) -> Decimal:
        """Cálculo de comissão por faixa única usando dados mock"""
        valor_float = float(valor_venda)
        
        # Buscar regras da loja
        regras_loja = [r for r in self.mock_comissao_regras 
                      if r["loja_id"] == loja_id and r["tipo_comissao"] == "VENDEDOR"]
        
        if not regras_loja:
            # Fallback se não encontrar regras
            if valor_float <= 25000:
                return valor_venda * Decimal('0.05')
            elif valor_float <= 50000:
                return valor_venda * Decimal('0.06')
            else:
                return valor_venda * Decimal('0.08')
        
        # Aplicar regras encontradas
        for regra in sorted(regras_loja, key=lambda x: x["ordem"]):
            valor_min = regra["valor_minimo"]
            valor_max = regra["valor_maximo"]
            
            if valor_max is None:  # Faixa infinita
                if valor_float >= valor_min:
                    return valor_venda * Decimal(str(regra["percentual"]))
            else:
                if valor_min <= valor_float <= valor_max:
                    return valor_venda * Decimal(str(regra["percentual"]))
        
        # Fallback
        return valor_venda * Decimal('0.06')

    async def buscar_dados_iniciais(self) -> TestResponse:
        """Retorna dados mock iniciais"""
        return TestResponse(
            success=True,
            message="Dados mock carregados",
            data={
                "lojas": self.mock_lojas,
                "equipe": self.mock_equipe,
                "configuracoes": self.mock_configs
            }
        )

    async def criar_cliente_teste(self, dados: TestClienteCreate) -> TestResponse:
        """Criar cliente mock"""
        # Verificar se loja existe
        loja = next((l for l in self.mock_lojas if l["id"] == dados.loja_id), None)
        if not loja:
            return TestResponse(
                success=False,
                message=f"Loja {dados.loja_id} não encontrada",
                errors=[f"Loja ID {dados.loja_id} não existe nos dados mock"]
            )

        # Criar cliente mock
        cliente_mock = {
            "id": str(uuid.uuid4()),
            "nome": dados.nome,
            "cpf_cnpj": dados.cpf_cnpj,
            "telefone": dados.telefone,
            "email": dados.email,
            "endereco": dados.endereco,
            "cidade": dados.cidade,
            "cep": dados.cep,
            "loja_id": dados.loja_id,
            "tipo_venda": dados.tipo_venda.value,
            "observacao": dados.observacao,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.created_clientes.append(cliente_mock)
        
        return TestResponse(
            success=True,
            message=f"Cliente mock criado na loja {loja['nome']}",
            data={
                "cliente": cliente_mock,
                "loja": loja["nome"]
            }
        )

    async def listar_clientes_teste(self, loja_id: str) -> TestResponse:
        """Listar clientes mock por loja"""
        clientes_loja = [c for c in self.created_clientes if c["loja_id"] == loja_id]
        
        return TestResponse(
            success=True,
            message=f"Clientes mock encontrados para loja {loja_id}",
            data={
                "clientes": clientes_loja,
                "total": len(clientes_loja),
                "loja_id": loja_id
            }
        )

    async def criar_ambiente_teste(self, dados: TestAmbienteCreate) -> TestResponse:
        """Criar ambiente mock"""
        ambiente_mock = {
            "id": str(uuid.uuid4()),
            "nome_ambiente": dados.nome_ambiente,
            "nome_cliente": dados.nome_cliente,
            "valor_total": float(dados.valor_total),
            "linha_produto": dados.linha_produto,
            "descricao_completa": dados.descricao_completa,
            "detalhes_xml": dados.detalhes_xml,
            "loja_id": dados.loja_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.created_ambientes.append(ambiente_mock)
        
        return TestResponse(
            success=True,
            message="Ambiente mock criado",
            data={"ambiente": ambiente_mock}
        )

    async def calcular_custos_engine(
        self, 
        valor_ambientes: Decimal,
        desconto_percentual: Decimal,
        loja_id: str,
        vendedor_id: str,
        custos_adicionais: List[Dict[str, Any]]
    ) -> TestResponse:
        """Engine de cálculo mock"""
        
        # Configurações mock
        config = next((c for c in self.mock_configs if c["loja_id"] == loja_id), self.mock_configs[0])
        
        deflator = Decimal(str(config["deflator_custo_fabrica"]))
        valor_medidor = Decimal(str(config["valor_medidor_padrao"]))
        frete_percentual = Decimal(str(config["valor_frete_percentual"]))
        
        # Calcular valor final após desconto
        valor_final = valor_ambientes * (1 - desconto_percentual / 100)
        
        # Cálculos de custos
        custo_fabrica = valor_ambientes * deflator
        comissao_vendedor = self.calcular_comissao_faixa_unica(valor_final, loja_id, vendedor_id)
        comissao_gerente = comissao_vendedor * Decimal('0.10')  # 10% da comissão do vendedor
        custo_medidor = valor_medidor
        custo_montador = valor_final * Decimal('0.05')  # 5% estimado
        custo_frete = valor_final * frete_percentual
        
        # Custos adicionais
        total_custos_adicionais = sum(Decimal(str(custo.get('valor', 0))) for custo in custos_adicionais)
        
        # Margem = Valor Final - Todos os Custos
        total_custos = (custo_fabrica + comissao_vendedor + comissao_gerente + 
                      custo_medidor + custo_montador + custo_frete + total_custos_adicionais)
        margem_lucro = valor_final - total_custos
        
        resultado = {
            'custo_fabrica': float(custo_fabrica),
            'comissao_vendedor': float(comissao_vendedor),
            'comissao_gerente': float(comissao_gerente),
            'custo_medidor': float(custo_medidor),
            'custo_montador': float(custo_montador),
            'custo_frete': float(custo_frete),
            'custos_adicionais': float(total_custos_adicionais),
            'margem_lucro': float(margem_lucro),
            'valor_final': float(valor_final),
            'total_custos': float(total_custos)
        }

        return TestResponse(
            success=True,
            message="Cálculo mock realizado com sucesso",
            data={
                'custos': resultado,
                'entrada': {
                    'valor_ambientes': float(valor_ambientes),
                    'desconto_percentual': float(desconto_percentual),
                    'loja_id': loja_id,
                    'vendedor_id': vendedor_id,
                    'custos_adicionais_count': len(custos_adicionais)
                }
            }
        )

    async def criar_orcamento_teste(self, dados: TestOrcamentoCreate) -> TestResponse:
        """Criar orçamento mock"""
        
        # Verificar cliente
        cliente = next((c for c in self.created_clientes if c["id"] == dados.cliente_id), None)
        if not cliente:
            return TestResponse(
                success=False,
                message="Cliente não encontrado nos dados mock",
                errors=[f"Cliente {dados.cliente_id} não existe"]
            )
        
        # Verificar ambientes
        ambientes_encontrados = [a for a in self.created_ambientes if a["id"] in dados.ambientes_ids]
        if len(ambientes_encontrados) != len(dados.ambientes_ids):
            return TestResponse(
                success=False,
                message="Alguns ambientes não foram encontrados",
                errors=[f"Esperados: {len(dados.ambientes_ids)}, encontrados: {len(ambientes_encontrados)}"]
            )
        
        # Calcular valores
        valor_ambientes = sum(Decimal(str(amb["valor_total"])) for amb in ambientes_encontrados)
        valor_final = valor_ambientes * (1 - dados.desconto_percentual / 100)
        
        # Usar engine de cálculo
        calculo_resultado = await self.calcular_custos_engine(
            valor_ambientes=valor_ambientes,
            desconto_percentual=dados.desconto_percentual,
            loja_id=dados.loja_id,
            vendedor_id=dados.vendedor_id,
            custos_adicionais=dados.custos_adicionais or []
        )
        
        if not calculo_resultado.success:
            return calculo_resultado
            
        custos_calculados = calculo_resultado.data['custos']
        
        # Gerar número mock
        config = next((c for c in self.mock_configs if c["loja_id"] == dados.loja_id), self.mock_configs[0])
        numero = f"{config.get('prefixo_numeracao', 'T-')}{config['proximo_numero_orcamento']:03d}"
        
        # Criar orçamento mock
        orcamento_mock = {
            "id": str(uuid.uuid4()),
            "numero": numero,
            "cliente_id": dados.cliente_id,
            "loja_id": dados.loja_id,
            "vendedor_id": dados.vendedor_id,
            "valor_ambientes": float(valor_ambientes),
            "desconto_percentual": float(dados.desconto_percentual),
            "valor_final": float(valor_final),
            "custo_fabrica": custos_calculados['custo_fabrica'],
            "comissao_vendedor": custos_calculados['comissao_vendedor'],
            "comissao_gerente": custos_calculados['comissao_gerente'],
            "custo_medidor": custos_calculados['custo_medidor'],
            "custo_montador": custos_calculados['custo_montador'],
            "custo_frete": custos_calculados['custo_frete'],
            "margem_lucro": custos_calculados['margem_lucro'],
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.created_orcamentos.append(orcamento_mock)
        
        return TestResponse(
            success=True,
            message="Orçamento mock criado com sucesso",
            data={
                "orcamento": orcamento_mock,
                "custos_detalhados": custos_calculados,
                "ambientes_incluidos": len(dados.ambientes_ids),
                "custos_adicionais": len(dados.custos_adicionais or [])
            }
        )

    async def listar_orcamentos_teste(self, loja_id: str) -> TestResponse:
        """Listar orçamentos mock por loja"""
        orcamentos_loja = [o for o in self.created_orcamentos if o["loja_id"] == loja_id]
        
        return TestResponse(
            success=True,
            message=f"Orçamentos mock encontrados para loja {loja_id}",
            data={
                "orcamentos": orcamentos_loja,
                "total": len(orcamentos_loja),
                "loja_id": loja_id
            }
        )

    async def testar_rls_isolamento(self, loja_origem: str, loja_destino: str) -> TestResponse:
        """Simular teste RLS"""
        return TestResponse(
            success=True,
            message="Teste RLS mock executado",
            data={
                "loja_origem": loja_origem,
                "loja_destino": loja_destino,
                "clientes_acessados": 0,  # Mock: RLS bloquearia acesso
                "orcamentos_acessados": 0,  # Mock: RLS bloquearia acesso
                "aviso": "Teste mock - RLS deve ser configurado no Supabase real"
            }
        ) 