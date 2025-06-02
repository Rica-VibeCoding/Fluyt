"""
Service para testes temporários - SEM AUTENTICAÇÃO!

⚠️ ATENÇÃO: Este service executa operações SEM validação de JWT!
Usar APENAS para testes de desenvolvimento!
"""

import uuid
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime

from ..shared.database import get_supabase_client
from .schemas import (
    TestClienteCreate, 
    TestAmbienteCreate, 
    TestOrcamentoCreate, 
    TestCalculoEngine,
    TestResponse
)

class TestService:
    def __init__(self):
        self._supabase = None

    @property
    def supabase(self):
        """Lazy loading do cliente Supabase"""
        if self._supabase is None:
            try:
                self._supabase = get_supabase_client()
            except ValueError as e:
                # Para testes, vamos simular dados se não houver Supabase configurado
                raise ValueError(f"Supabase não configurado: {e}")
        return self._supabase

    def calcular_comissao_faixa_unica(self, valor_venda: Decimal, loja_id: str, vendedor_id: str) -> Decimal:
        """Cálculo de comissão por faixa única - TEMPORÁRIO para teste"""
        try:
            # Buscar regras de comissão da loja
            regras_response = self.supabase.table('config_regras_comissao_faixa')\
                .select('*')\
                .eq('loja_id', loja_id)\
                .eq('tipo_comissao', 'VENDEDOR')\
                .order('ordem')\
                .execute()
            
            if not regras_response.data:
                # Regras padrão se não houver configuração
                if valor_venda <= 25000:
                    return valor_venda * Decimal('0.05')  # 5%
                elif valor_venda <= 50000:
                    return valor_venda * Decimal('0.06')  # 6%
                else:
                    return valor_venda * Decimal('0.08')  # 8%
            
            # Aplicar regras configuradas
            for regra in regras_response.data:
                valor_min = Decimal(str(regra['valor_minimo']))
                valor_max = regra['valor_maximo']
                
                if valor_max is None:  # Faixa infinita
                    if valor_venda >= valor_min:
                        percentual = Decimal(str(regra['percentual']))
                        return valor_venda * percentual
                else:
                    valor_max = Decimal(str(valor_max))
                    if valor_min <= valor_venda <= valor_max:
                        percentual = Decimal(str(regra['percentual']))
                        return valor_venda * percentual
            
            # Se não encontrou faixa, usar 5% padrão
            return valor_venda * Decimal('0.05')
            
        except Exception as e:
            # Fallback em caso de erro
            return valor_venda * Decimal('0.06')  # 6% padrão

    async def criar_cliente_teste(self, dados: TestClienteCreate) -> TestResponse:
        """Criar cliente para teste - SEM JWT"""
        try:
            # Verificar se a loja existe
            loja_response = self.supabase.table('c_lojas').select('*').eq('id', dados.loja_id).execute()
            if not loja_response.data:
                return TestResponse(
                    success=False,
                    message=f"Loja {dados.loja_id} não encontrada",
                    errors=[f"Loja ID {dados.loja_id} não existe na base de dados"]
                )

            # Dados do cliente
            cliente_data = {
                'id': str(uuid.uuid4()),
                'nome': dados.nome,
                'cpf_cnpj': dados.cpf_cnpj,
                'telefone': dados.telefone,
                'email': dados.email,
                'endereco': dados.endereco,
                'cidade': dados.cidade,
                'cep': dados.cep,
                'loja_id': dados.loja_id,
                'tipo_venda': dados.tipo_venda.value,
                'observacao': dados.observacao,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            # Inserir cliente
            response = self.supabase.table('c_clientes').insert(cliente_data).execute()
            
            if response.data:
                return TestResponse(
                    success=True,
                    message=f"Cliente criado com sucesso na loja {loja_response.data[0]['nome']}",
                    data={
                        'cliente': response.data[0],
                        'loja': loja_response.data[0]['nome']
                    }
                )
            else:
                return TestResponse(
                    success=False,
                    message="Erro ao criar cliente",
                    errors=["Falha na inserção no banco de dados"]
                )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro interno ao criar cliente",
                errors=[str(e)]
            )

    async def listar_clientes_teste(self, loja_id: str) -> TestResponse:
        """Listar clientes por loja - Teste RLS"""
        try:
            # Buscar clientes da loja específica
            response = self.supabase.table('c_clientes')\
                .select('*, c_lojas(nome)')\
                .eq('loja_id', loja_id)\
                .execute()

            return TestResponse(
                success=True,
                message=f"Clientes encontrados para loja {loja_id}",
                data={
                    'clientes': response.data,
                    'total': len(response.data),
                    'loja_id': loja_id
                }
            )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro ao listar clientes",
                errors=[str(e)]
            )

    async def criar_ambiente_teste(self, dados: TestAmbienteCreate) -> TestResponse:
        """Criar ambiente para teste"""
        try:
            ambiente_data = {
                'id': str(uuid.uuid4()),
                'nome_ambiente': dados.nome_ambiente,
                'nome_cliente': dados.nome_cliente,
                'valor_total': float(dados.valor_total),
                'linha_produto': dados.linha_produto,
                'descricao_completa': dados.descricao_completa,
                'detalhes_xml': dados.detalhes_xml,
                'loja_id': dados.loja_id,
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.supabase.table('c_ambientes').insert(ambiente_data).execute()
            
            return TestResponse(
                success=True,
                message="Ambiente criado com sucesso",
                data={'ambiente': response.data[0]}
            )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro ao criar ambiente",
                errors=[str(e)]
            )

    async def criar_orcamento_teste(self, dados: TestOrcamentoCreate) -> TestResponse:
        """Criar orçamento completo com cálculos"""
        try:
            # 1. Verificar se cliente existe
            cliente_response = self.supabase.table('c_clientes')\
                .select('*')\
                .eq('id', dados.cliente_id)\
                .eq('loja_id', dados.loja_id)\
                .execute()
            
            if not cliente_response.data:
                return TestResponse(
                    success=False,
                    message="Cliente não encontrado ou não pertence à loja",
                    errors=[f"Cliente {dados.cliente_id} não encontrado na loja {dados.loja_id}"]
                )

            # 2. Verificar ambientes
            ambientes_response = self.supabase.table('c_ambientes')\
                .select('*')\
                .in_('id', dados.ambientes_ids)\
                .eq('loja_id', dados.loja_id)\
                .execute()
            
            if len(ambientes_response.data) != len(dados.ambientes_ids):
                return TestResponse(
                    success=False,
                    message="Alguns ambientes não foram encontrados",
                    errors=[f"Ambientes esperados: {len(dados.ambientes_ids)}, encontrados: {len(ambientes_response.data)}"]
                )

            # 3. Calcular valores
            valor_ambientes = sum(Decimal(str(amb['valor_total'])) for amb in ambientes_response.data)
            valor_final = valor_ambientes * (1 - dados.desconto_percentual / 100)

            # 4. Usar engine de cálculo
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

            # 5. Gerar número do orçamento
            config_response = self.supabase.table('config_loja')\
                .select('proximo_numero_orcamento, prefixo_numeracao')\
                .eq('loja_id', dados.loja_id)\
                .execute()
            
            if config_response.data:
                numero = f"{config_response.data[0].get('prefixo_numeracao', '')}{config_response.data[0]['proximo_numero_orcamento']}"
                # Incrementar próximo número
                self.supabase.table('config_loja')\
                    .update({'proximo_numero_orcamento': config_response.data[0]['proximo_numero_orcamento'] + 1})\
                    .eq('loja_id', dados.loja_id)\
                    .execute()
            else:
                numero = "TESTE-001"

            # 6. Criar orçamento
            orcamento_data = {
                'id': str(uuid.uuid4()),
                'numero': numero,
                'cliente_id': dados.cliente_id,
                'loja_id': dados.loja_id,
                'vendedor_id': dados.vendedor_id,
                'valor_ambientes': float(valor_ambientes),
                'desconto_percentual': float(dados.desconto_percentual),
                'valor_final': float(valor_final),
                'custo_fabrica': custos_calculados['custo_fabrica'],
                'comissao_vendedor': custos_calculados['comissao_vendedor'],
                'comissao_gerente': custos_calculados['comissao_gerente'],
                'custo_medidor': custos_calculados['custo_medidor'],
                'custo_montador': custos_calculados['custo_montador'],
                'custo_frete': custos_calculados['custo_frete'],
                'margem_lucro': custos_calculados['margem_lucro'],
                'medidor_selecionado_id': dados.medidor_selecionado_id,
                'montador_selecionado_id': dados.montador_selecionado_id,
                'transportadora_selecionada_id': dados.transportadora_selecionada_id,
                'necessita_aprovacao': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            orcamento_response = self.supabase.table('c_orcamentos').insert(orcamento_data).execute()
            orcamento_id = orcamento_response.data[0]['id']

            # 7. Relacionar ambientes
            for ambiente_id in dados.ambientes_ids:
                self.supabase.table('c_orcamento_ambientes').insert({
                    'id': str(uuid.uuid4()),
                    'orcamento_id': orcamento_id,
                    'ambiente_id': ambiente_id,
                    'incluido': True
                }).execute()

            # 8. Inserir custos adicionais se houver
            if dados.custos_adicionais:
                for custo in dados.custos_adicionais:
                    self.supabase.table('c_orcamento_custos_adicionais').insert({
                        'id': str(uuid.uuid4()),
                        'orcamento_id': orcamento_id,
                        'descricao_custo': custo.get('descricao', ''),
                        'valor_custo': float(custo.get('valor', 0))
                    }).execute()

            return TestResponse(
                success=True,
                message="Orçamento criado com sucesso",
                data={
                    'orcamento': orcamento_response.data[0],
                    'custos_detalhados': custos_calculados,
                    'ambientes_incluidos': len(dados.ambientes_ids),
                    'custos_adicionais': len(dados.custos_adicionais or [])
                }
            )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro ao criar orçamento",
                errors=[str(e)]
            )

    async def calcular_custos_engine(
        self, 
        valor_ambientes: Decimal,
        desconto_percentual: Decimal,
        loja_id: str,
        vendedor_id: str,
        custos_adicionais: List[Dict[str, Any]]
    ) -> TestResponse:
        """Testar engine de cálculo isoladamente - VERSÃO SIMPLIFICADA"""
        try:
            # Buscar configurações da loja
            config_response = self.supabase.table('config_loja')\
                .select('*')\
                .eq('loja_id', loja_id)\
                .execute()
            
            # Valores padrão se não houver configuração
            if config_response.data:
                config = config_response.data[0]
                deflator = Decimal(str(config.get('deflator_custo_fabrica', 0.40)))
                valor_medidor = Decimal(str(config.get('valor_medidor_padrao', 200)))
                frete_percentual = Decimal(str(config.get('valor_frete_percentual', 0.02)))
            else:
                deflator = Decimal('0.40')  # 40%
                valor_medidor = Decimal('200')
                frete_percentual = Decimal('0.02')  # 2%
            
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
                message="Cálculo realizado com sucesso",
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

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro no engine de cálculo",
                errors=[str(e)]
            )

    async def listar_orcamentos_teste(self, loja_id: str) -> TestResponse:
        """Listar orçamentos por loja - Teste RLS"""
        try:
            response = self.supabase.table('c_orcamentos')\
                .select('''
                    *,
                    c_clientes(nome, cpf_cnpj),
                    cad_equipe(nome),
                    c_lojas(nome)
                ''')\
                .eq('loja_id', loja_id)\
                .execute()

            return TestResponse(
                success=True,
                message=f"Orçamentos encontrados para loja {loja_id}",
                data={
                    'orcamentos': response.data,
                    'total': len(response.data),
                    'loja_id': loja_id
                }
            )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro ao listar orçamentos",
                errors=[str(e)]
            )

    async def testar_rls_isolamento(self, loja_origem: str, loja_destino: str) -> TestResponse:
        """Testar se RLS impede acesso cross-loja"""
        try:
            # Tentar acessar clientes de outra loja
            clientes_response = self.supabase.table('c_clientes')\
                .select('*')\
                .eq('loja_id', loja_destino)\
                .execute()

            # Tentar acessar orçamentos de outra loja  
            orcamentos_response = self.supabase.table('c_orcamentos')\
                .select('*')\
                .eq('loja_id', loja_destino)\
                .execute()

            return TestResponse(
                success=True,
                message="Teste RLS executado",
                data={
                    'loja_origem': loja_origem,
                    'loja_destino': loja_destino,
                    'clientes_acessados': len(clientes_response.data),
                    'orcamentos_acessados': len(orcamentos_response.data),
                    'aviso': "RLS deve estar configurado no Supabase para funcionar corretamente"
                }
            )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro no teste RLS",
                errors=[str(e)]
            )

    async def buscar_dados_iniciais(self) -> TestResponse:
        """Buscar dados necessários para testes"""
        try:
            # Buscar lojas
            lojas = self.supabase.table('c_lojas').select('*').execute()
            
            # Buscar equipe
            equipe = self.supabase.table('cad_equipe').select('*').execute()
            
            # Buscar configurações
            configs = self.supabase.table('config_loja').select('*').execute()
            
            return TestResponse(
                success=True,
                message="Dados iniciais carregados",
                data={
                    'lojas': lojas.data,
                    'equipe': equipe.data,
                    'configuracoes': configs.data
                }
            )

        except Exception as e:
            return TestResponse(
                success=False,
                message="Erro ao buscar dados iniciais",
                errors=[str(e)]
            ) 