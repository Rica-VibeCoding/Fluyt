# Business logic helpers for orcamentos

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from decimal import Decimal
from datetime import datetime
import uuid
import json

from .repository import OrcamentoRepository
from .schemas import OrcamentoCreate, OrcamentoUpdate, OrcamentoResponse, OrcamentoListItem, OrcamentoFilters, SolicitacaoAprovacao, CalculoCustos, RelatorioMargem

# Configurar logger
logger = logging.getLogger(__name__)


class OrcamentoService:
    """
    Service layer para orçamentos - orquestra cálculos completos
    Stack: FastAPI + Python + Pandas (conforme PRD.md)
    
    Responsabilidade: Lógica de negócio, cálculos, validações
    """
    
    def __init__(self, repository: OrcamentoRepository):
        self.repository = repository
    
    def calcular_comissao_progressiva_pandas(self, valor_venda: float, regras_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Engine de cálculo de comissão progressiva usando Pandas (conforme stack documentado)
        Implementação EXATA do algoritmo especificado no PRD.md
        
        Args:
            valor_venda (float): Valor da venda para calcular comissão
            regras_df (pd.DataFrame): DataFrame com regras de comissão por faixa
            
        Returns:
            Dict[str, Any]: Resultado do cálculo com detalhamento
            
        Algoritmo conforme PRD.md:
        ```
        def calcular_comissao(valor_venda, regras):
            comissao_calculada = 0
            for regra in regras:
                if valor_atingido_pela_faixa(valor_venda, regra.valor_minimo, regra.valor_maximo):
                     comissao_calculada += calcular_valor_da_faixa(...)
            return comissao_calculada
        ```
        """
        if regras_df.empty:
            logger.warning("DataFrame de regras vazio, retornando comissão zero")
            return {
                'comissao_total': 0.0,
                'detalhes_faixas': [],
                'valor_total_processado': valor_venda
            }
        
        logger.debug(f"Iniciando cálculo progressivo para valor: R$ {valor_venda:,.2f}")
        
        # Implementação EXATA conforme PRD.md
        comissao_calculada = 0.0
        detalhes_faixas = []
        
        # Processar cada regra usando lógica do PRD.md
        for idx, regra in regras_df.iterrows():
            if self._valor_atingido_pela_faixa(valor_venda, regra['valor_minimo'], regra['valor_maximo']):
                valor_faixa, comissao_faixa = self._calcular_valor_da_faixa(
                    valor_venda, 
                    regra['valor_minimo'], 
                    regra['valor_maximo'], 
                    regra['percentual']
                )
                
                if comissao_faixa > 0:
                    comissao_calculada += comissao_faixa
                    
                    # Detalhar para auditoria
                    detalhe = {
                        'faixa': int(regra['ordem']),
                        'valor_minimo': float(regra['valor_minimo']),
                        'valor_maximo': float(regra['valor_maximo']) if pd.notna(regra['valor_maximo']) else None,
                        'valor_faixa': float(valor_faixa),
                        'percentual': float(regra['percentual']),
                        'comissao_faixa': float(comissao_faixa)
                    }
                    detalhes_faixas.append(detalhe)
                    
                    logger.debug(f"Faixa {regra['ordem']}: R$ {valor_faixa:,.2f} × {regra['percentual']:.1%} = R$ {comissao_faixa:,.2f}")
        
        resultado = {
            'comissao_total': float(comissao_calculada),
            'detalhes_faixas': detalhes_faixas,
            'valor_total_processado': float(valor_venda)
        }
        
        logger.info(f"Cálculo concluído: R$ {valor_venda:,.2f} → R$ {comissao_calculada:,.2f} ({len(detalhes_faixas)} faixas)")
        return resultado
    
    def _valor_atingido_pela_faixa(self, valor_venda: float, valor_minimo: float, valor_maximo: Optional[float]) -> bool:
        """
        Verifica se o valor da venda atinge esta faixa de comissão
        Implementa a lógica: valor_atingido_pela_faixa(valor_venda, regra.valor_minimo, regra.valor_maximo)
        
        Args:
            valor_venda: Valor total da venda
            valor_minimo: Valor mínimo da faixa
            valor_maximo: Valor máximo da faixa (None = infinito)
            
        Returns:
            bool: True se valor_venda está dentro desta faixa
            
        Exemplo:
        - Faixa: R$ 10.000 → R$ 25.000
        - Venda: R$ 30.000
        - Retorna: True (porque parte da venda está nesta faixa)
        """
        # Se venda não atingiu nem o mínimo desta faixa
        if valor_venda <= valor_minimo:
            return False
            
        # Venda atingiu pelo menos o valor mínimo desta faixa
        return True
    
    def _calcular_valor_da_faixa(
        self, 
        valor_venda: float, 
        valor_minimo: float, 
        valor_maximo: Optional[float], 
        percentual: float
    ) -> tuple[float, float]:
        """
        Calcula o valor aplicável e comissão para uma faixa específica
        Implementa: calcular_valor_da_faixa(valor_venda, regra.valor_minimo, regra.valor_maximo, regra.percentual)
        
        Args:
            valor_venda: Valor total da venda
            valor_minimo: Valor mínimo da faixa
            valor_maximo: Valor máximo da faixa (None = infinito)
            percentual: Percentual de comissão da faixa
            
        Returns:
            tuple[float, float]: (valor_aplicavel_na_faixa, comissao_da_faixa)
            
        Exemplo:
        - Venda: R$ 30.000
        - Faixa: R$ 10.000 → R$ 25.000 (5%)
        - Valor aplicável: R$ 15.000 (25.000 - 10.000)
        - Comissão: R$ 750 (15.000 × 5%)
        """
        # Determinar valor máximo efetivo (infinito se None)
        valor_max_efetivo = valor_maximo if valor_maximo is not None and not pd.isna(valor_maximo) else float('inf')
        
        # Calcular valor aplicável nesta faixa
        valor_inicio_faixa = max(valor_venda, valor_minimo)  # Onde começamos nesta faixa
        valor_fim_faixa = min(valor_venda, valor_max_efetivo)  # Onde terminamos nesta faixa
        
        # Valor efetivamente dentro desta faixa
        valor_aplicavel = max(0, valor_fim_faixa - valor_minimo)
        
        # Comissão desta faixa
        comissao_faixa = valor_aplicavel * percentual
        
        logger.debug(f"Faixa R$ {valor_minimo:,.0f} → R$ {valor_max_efetivo if valor_max_efetivo != float('inf') else '∞'}: valor aplicável R$ {valor_aplicavel:,.2f}")
        
        return valor_aplicavel, comissao_faixa
    
    async def calcular_orcamento_completo(self, dados_orcamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula orçamento completo com todos os custos usando engine Pandas
        
        Args:
            dados_orcamento: {
                'loja_id': str,
                'vendedor_id': str,
                'valor_ambientes': float,
                'desconto_percentual': float,
                'custos_adicionais': List[Dict] (opcional),
                'medidor_id': str (opcional),
                'montador_id': str (opcional),
                'transportadora_id': str (opcional)
            }
            
        Returns:
            Dict[str, Any]: Cálculo completo com todos os custos e margem
            
        Exemplo de retorno:
        {
            'valor_ambientes': 50000.0,
            'desconto_percentual': 0.20,
            'valor_final': 40000.0,
            'custos': {
                'custo_fabrica': 14000.0,
                'comissao_vendedor': 2150.0,
                'comissao_gerente': 1200.0,
                'custo_medidor': 200.0,
                'custo_montador': 1000.0,
                'custo_frete': 800.0,
                'custos_adicionais': 500.0,
                'total_custos': 19850.0
            },
            'margem_lucro': 20150.0,
            'percentual_margem': 50.38,
            'detalhes_calculo': {...}
        }
        """
        try:
            loja_id = dados_orcamento['loja_id']
            vendedor_id = dados_orcamento['vendedor_id']
            valor_ambientes = float(dados_orcamento['valor_ambientes'])
            desconto_percentual = float(dados_orcamento.get('desconto_percentual', 0.0))
            
            # Calcular valor final após desconto
            valor_final = valor_ambientes * (1 - desconto_percentual)
            
            logger.info(f"Iniciando cálculo completo: R$ {valor_ambientes:,.2f} → R$ {valor_final:,.2f} (desconto {desconto_percentual:.1%})")
            
            # 1. Buscar configurações da loja usando Pandas
            config = await self.repository.get_config_loja(loja_id)
            
            # 2. Calcular todos os custos
            custos = await self._calcular_todos_custos(
                loja_id=loja_id,
                vendedor_id=vendedor_id,
                valor_ambientes=valor_ambientes,
                valor_final=valor_final,
                config=config,
                dados_orcamento=dados_orcamento
            )
            
            # 3. Calcular margem final
            total_custos = sum(custos['detalhes'].values())
            margem_lucro = valor_final - total_custos
            percentual_margem = (margem_lucro / valor_final * 100) if valor_final > 0 else 0
            
            # 4. Montar resultado completo
            resultado = {
                'valor_ambientes': valor_ambientes,
                'desconto_percentual': desconto_percentual,
                'valor_final': valor_final,
                'custos': {
                    **custos['detalhes'],
                    'total_custos': total_custos
                },
                'margem_lucro': margem_lucro,
                'percentual_margem': percentual_margem,
                'detalhes_calculo': {
                    'config_snapshot': config,
                    'comissao_vendedor_detalhes': custos['detalhes_comissao_vendedor'],
                    'comissao_gerente_detalhes': custos['detalhes_comissao_gerente'],
                    'timestamp_calculo': datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Cálculo concluído: Margem R$ {margem_lucro:,.2f} ({percentual_margem:.2f}%)")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro no cálculo completo do orçamento: {str(e)}")
            raise Exception(f"Erro ao calcular orçamento: {str(e)}")

    async def _calcular_todos_custos(
        self, 
        loja_id: str, 
        vendedor_id: str,
        valor_ambientes: float,
        valor_final: float,
        config: Dict[str, Any],
        dados_orcamento: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula todos os custos do orçamento usando engine Pandas
        
        Returns:
            Dict com custos detalhados e cálculos de comissão
        """
        custos_detalhes = {}
        
        # 1. Custo de fábrica (valor XML × deflator)
        deflator = float(config['deflator_custo_fabrica'])
        custo_fabrica = valor_ambientes * deflator
        custos_detalhes['custo_fabrica'] = custo_fabrica
        logger.debug(f"Custo fábrica: R$ {valor_ambientes:,.2f} × {deflator:.1%} = R$ {custo_fabrica:,.2f}")
        
        # 2. Comissão vendedor (progressiva com Pandas)
        regras_vendedor_df = await self.repository.get_regras_comissao(loja_id, 'VENDEDOR')
        comissao_vendedor_calc = self.calcular_comissao_progressiva_pandas(valor_final, regras_vendedor_df)
        custos_detalhes['comissao_vendedor'] = comissao_vendedor_calc['comissao_total']
        
        # 3. Comissão gerente (progressiva com Pandas) 
        regras_gerente_df = await self.repository.get_regras_comissao(loja_id, 'GERENTE')
        comissao_gerente_calc = self.calcular_comissao_progressiva_pandas(valor_final, regras_gerente_df)
        custos_detalhes['comissao_gerente'] = comissao_gerente_calc['comissao_total']
        
        # 4. Custo medidor
        custo_medidor = float(config['valor_medidor_padrao'])
        custos_detalhes['custo_medidor'] = custo_medidor
        
        # 5. Custo frete (percentual sobre valor final)
        percentual_frete = float(config['valor_frete_percentual'])
        custo_frete = valor_final * percentual_frete
        custos_detalhes['custo_frete'] = custo_frete
        logger.debug(f"Custo frete: R$ {valor_final:,.2f} × {percentual_frete:.1%} = R$ {custo_frete:,.2f}")
        
        # 6. Custo montador (se especificado)
        custo_montador = dados_orcamento.get('custo_montador', 0.0)
        custos_detalhes['custo_montador'] = float(custo_montador)
        
        # 7. Custos adicionais (soma de múltiplos itens)
        custos_adicionais_lista = dados_orcamento.get('custos_adicionais', [])
        total_custos_adicionais = sum(float(item.get('valor_custo', 0)) for item in custos_adicionais_lista)
        custos_detalhes['custos_adicionais'] = total_custos_adicionais
        
        if custos_adicionais_lista:
            logger.debug(f"Custos adicionais: {len(custos_adicionais_lista)} itens = R$ {total_custos_adicionais:,.2f}")
        
        return {
            'detalhes': custos_detalhes,
            'detalhes_comissao_vendedor': comissao_vendedor_calc,
            'detalhes_comissao_gerente': comissao_gerente_calc
        }

    async def validar_limite_desconto(self, loja_id: str, vendedor_id: str, desconto_percentual: float) -> Dict[str, Any]:
        """
        Valida se desconto está dentro dos limites configurados
        
        Args:
            loja_id: ID da loja
            vendedor_id: ID do vendedor
            desconto_percentual: Percentual de desconto (ex: 0.15 = 15%)
            
        Returns:
            Dict com validação e necessidade de aprovação
        """
        try:
            config = await self.repository.get_config_loja(loja_id)
            
            limite_vendedor = float(config['limite_desconto_vendedor'])
            limite_gerente = float(config['limite_desconto_gerente'])
            
            resultado = {
                'desconto_solicitado': desconto_percentual,
                'limite_vendedor': limite_vendedor,
                'limite_gerente': limite_gerente,
                'aprovado_automaticamente': False,
                'necessita_aprovacao': False,
                'nivel_aprovacao_necessario': None
            }
            
            if desconto_percentual <= limite_vendedor:
                resultado['aprovado_automaticamente'] = True
                logger.debug(f"Desconto {desconto_percentual:.1%} aprovado automaticamente (limite vendedor: {limite_vendedor:.1%})")
            elif desconto_percentual <= limite_gerente:
                resultado['necessita_aprovacao'] = True
                resultado['nivel_aprovacao_necessario'] = 'GERENTE'
                logger.info(f"Desconto {desconto_percentual:.1%} necessita aprovação do gerente (limite: {limite_gerente:.1%})")
            else:
                resultado['necessita_aprovacao'] = True
                resultado['nivel_aprovacao_necessario'] = 'ADMIN_MASTER'
                logger.info(f"Desconto {desconto_percentual:.1%} necessita aprovação do admin (acima de {limite_gerente:.1%})")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao validar limite de desconto: {str(e)}")
            raise Exception(f"Erro na validação de desconto: {str(e)}")

    async def criar_orcamento_completo(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria orçamento completo integrando cálculos e validações
        
        Args:
            dados: Dados completos do orçamento
            
        Returns:
            Dict com orçamento calculado e status de aprovação
        """
        try:
            # 1. Validar desconto
            validacao_desconto = await self.validar_limite_desconto(
                dados['loja_id'],
                dados['vendedor_id'], 
                dados.get('desconto_percentual', 0.0)
            )
            
            # 2. Calcular orçamento completo
            calculo = await self.calcular_orcamento_completo(dados)
            
            # 3. Montar resposta final
            orcamento_completo = {
                **calculo,
                'validacao_desconto': validacao_desconto,
                'necessita_aprovacao': validacao_desconto['necessita_aprovacao'],
                'nivel_aprovacao': validacao_desconto.get('nivel_aprovacao_necessario'),
                'status_orcamento': 'AGUARDANDO_APROVACAO' if validacao_desconto['necessita_aprovacao'] else 'APROVADO_AUTOMATICAMENTE'
            }
            
            logger.info(f"Orçamento criado: R$ {calculo['valor_final']:,.2f}, margem {calculo['percentual_margem']:.2f}%, status: {orcamento_completo['status_orcamento']}")
            
            return orcamento_completo
            
        except Exception as e:
            logger.error(f"Erro ao criar orçamento completo: {str(e)}")
            raise Exception(f"Erro na criação do orçamento: {str(e)}")

    def demo_calculo_comissao_prd(self) -> Dict[str, Any]:
        """
        DEMO: Teste do algoritmo conforme exemplo do PRD.md
        
        Exemplo do PRD: Venda R$ 40.000 deve resultar em R$ 2.150 de comissão
        Faixas exemplo:
        - R$ 0 → R$ 25.000 = 5%
        - R$ 25.001 → R$ 50.000 = 6%  
        - R$ 50.001 → ∞ = 8%
        
        Cálculo esperado: (25.000 × 5%) + (15.000 × 6%) = R$ 1.250 + R$ 900 = R$ 2.150
        
        Returns:
            Dict: Resultado do teste de validação
        """
        logger.info("🧪 DEMO: Testando algoritmo de comissão conforme PRD.md")
        
        # Criar DataFrame de teste com faixas do PRD.md
        regras_teste = pd.DataFrame([
            {
                'id': '1',
                'loja_id': 'test',
                'tipo_comissao': 'VENDEDOR',
                'valor_minimo': 0.0,
                'valor_maximo': 25000.0,
                'percentual': 0.05,  # 5%
                'ordem': 1
            },
            {
                'id': '2', 
                'loja_id': 'test',
                'tipo_comissao': 'VENDEDOR',
                'valor_minimo': 25000.01,
                'valor_maximo': 50000.0,
                'percentual': 0.06,  # 6%
                'ordem': 2
            },
            {
                'id': '3',
                'loja_id': 'test', 
                'tipo_comissao': 'VENDEDOR',
                'valor_minimo': 50000.01,
                'valor_maximo': None,  # Infinito
                'percentual': 0.08,  # 8%
                'ordem': 3
            }
        ])
        
        # Testar com valor do exemplo: R$ 40.000
        valor_teste = 40000.0
        resultado = self.calcular_comissao_progressiva_pandas(valor_teste, regras_teste)
        
        # Validar resultado
        esperado = 2150.0  # Conforme PRD.md
        atual = resultado['comissao_total']
        sucesso = abs(atual - esperado) < 0.01  # Margem de erro mínima
        
        demo_result = {
            'teste': 'Algoritmo PRD.md',
            'valor_venda': valor_teste,
            'comissao_esperada': esperado,
            'comissao_calculada': atual,
            'sucesso': sucesso,
            'diferenca': atual - esperado,
            'detalhes': resultado['detalhes_faixas'],
            'algoritmo_status': '✅ CORRETO' if sucesso else '❌ ERRO'
        }
        
        logger.info(f"🎯 DEMO Resultado: R$ {valor_teste:,.2f} → R$ {atual:,.2f} (esperado: R$ {esperado:,.2f}) - {demo_result['algoritmo_status']}")
        
        return demo_result

    # ===== MÉTODOS CRUD PARA CONTROLLERS =====
    
    async def criar_orcamento(self, orcamento_data: OrcamentoCreate, current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Cria novo orçamento com cálculos automáticos
        
        Args:
            orcamento_data: Dados do orçamento
            current_user: Usuário autenticado
            
        Returns:
            OrcamentoResponse: Orçamento criado com todos os cálculos
        """
        try:
            loja_id = current_user['loja_id']
            vendedor_id = current_user['user_id']
            
            logger.info(f"Criando orçamento para cliente {orcamento_data.cliente_id}, loja {loja_id}")
            
            # 1. Buscar valores dos ambientes
            valor_ambientes = await self.repository.calcular_valor_total_ambientes(orcamento_data.ambiente_ids)
            
            # 2. Calcular valor final com desconto
            desconto_decimal = float(orcamento_data.desconto_percentual) / 100
            valor_final = valor_ambientes * (1 - desconto_decimal)
            
            # 3. Validar limite de desconto
            validacao_desconto = await self.validar_limite_desconto(loja_id, vendedor_id, desconto_decimal)
            
            # 4. Calcular todos os custos
            dados_calculo = {
                'loja_id': loja_id,
                'vendedor_id': vendedor_id,
                'valor_ambientes': valor_ambientes,
                'valor_final': valor_final,
                'custos_adicionais': [
                    {'descricao_custo': c.descricao_custo, 'valor_custo': float(c.valor_custo)}
                    for c in (orcamento_data.custos_adicionais or [])
                ],
                'montador_id': str(orcamento_data.montador_selecionado_id),
                'medidor_id': str(orcamento_data.medidor_selecionado_id),
                'transportadora_id': str(orcamento_data.transportadora_selecionada_id)
            }
            
            calculo = await self.calcular_orcamento_completo(dados_calculo)
            
            # 5. Preparar dados para salvar
            orcamento_db = {
                'cliente_id': str(orcamento_data.cliente_id),
                'loja_id': loja_id,
                'vendedor_id': vendedor_id,
                'medidor_selecionado_id': str(orcamento_data.medidor_selecionado_id),
                'montador_selecionado_id': str(orcamento_data.montador_selecionado_id),
                'transportadora_selecionada_id': str(orcamento_data.transportadora_selecionada_id),
                'valor_ambientes': valor_ambientes,
                'desconto_percentual': desconto_decimal,
                'valor_final': valor_final,
                'custo_fabrica': calculo['custos']['custo_fabrica'],
                'comissao_vendedor': calculo['custos']['comissao_vendedor'],
                'comissao_gerente': calculo['custos']['comissao_gerente'],
                'custo_medidor': calculo['custos']['custo_medidor'],
                'custo_montador': calculo['custos']['custo_montador'],
                'custo_frete': calculo['custos']['custo_frete'],
                'margem_lucro': calculo['margem_lucro'],
                'necessita_aprovacao': validacao_desconto['necessita_aprovacao'],
                'plano_pagamento': json.dumps([p.dict() for p in orcamento_data.plano_pagamento]),
                'observacoes': orcamento_data.observacoes,
                'config_snapshot': json.dumps(calculo.get('config_snapshot', {}))
            }
            
            # 6. Salvar no banco
            orcamento_criado = await self.repository.criar_orcamento(orcamento_db)
            
            # 7. Salvar ambientes e custos adicionais
            await self.repository.salvar_orcamento_ambientes(orcamento_criado['id'], orcamento_data.ambiente_ids)
            
            if orcamento_data.custos_adicionais:
                await self.repository.salvar_custos_adicionais(orcamento_criado['id'], orcamento_data.custos_adicionais)
            
            logger.info(f"Orçamento {orcamento_criado['numero']} criado com sucesso")
            
            # 8. Retornar resposta formatada
            return await self._format_orcamento_response(orcamento_criado, current_user)
            
        except Exception as e:
            logger.error(f"Erro ao criar orçamento: {str(e)}")
            raise Exception(f"Erro ao criar orçamento: {str(e)}")
    
    async def listar_orcamentos(self, filters: OrcamentoFilters, current_user: Dict[str, Any], skip: int = 0, limit: int = 50) -> List[OrcamentoListItem]:
        """
        Lista orçamentos com filtros aplicados
        
        Args:
            filters: Filtros de busca
            current_user: Usuário autenticado
            skip: Registros para pular
            limit: Limite de registros
            
        Returns:
            List[OrcamentoListItem]: Lista de orçamentos
        """
        try:
            logger.debug(f"Listando orçamentos para usuário {current_user['perfil']}")
            
            # Aplicar filtros baseados no perfil
            if current_user['perfil'] == 'VENDEDOR':
                filters.vendedor_id = current_user['user_id']
            elif current_user['perfil'] in ['GERENTE']:
                # Gerente vê toda a loja
                pass
            elif current_user['perfil'] == 'ADMIN_MASTER':
                # Admin Master vê tudo
                pass
            
            orcamentos = await self.repository.listar_orcamentos(filters, current_user['loja_id'], skip, limit)
            
            return [OrcamentoListItem(**orc) for orc in orcamentos]
            
        except Exception as e:
            logger.error(f"Erro ao listar orçamentos: {str(e)}")
            raise Exception(f"Erro ao listar orçamentos: {str(e)}")
    
    async def obter_orcamento(self, orcamento_id: uuid.UUID, current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Obtém detalhes de um orçamento específico
        
        Args:
            orcamento_id: ID do orçamento
            current_user: Usuário autenticado
            
        Returns:
            OrcamentoResponse: Dados do orçamento
        """
        try:
            orcamento = await self.repository.obter_orcamento_por_id(str(orcamento_id))
            
            if not orcamento:
                raise Exception("Orçamento não encontrado")
            
            # Verificar permissões
            if not await self._verificar_permissao_orcamento(orcamento, current_user):
                raise Exception("Sem permissão para acessar este orçamento")
            
            return await self._format_orcamento_response(orcamento, current_user)
            
        except Exception as e:
            logger.error(f"Erro ao obter orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao obter orçamento: {str(e)}")
    
    async def atualizar_orcamento(self, orcamento_id: uuid.UUID, orcamento_data: OrcamentoUpdate, current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Atualiza um orçamento existente
        
        Args:
            orcamento_id: ID do orçamento
            orcamento_data: Dados para atualização
            current_user: Usuário autenticado
            
        Returns:
            OrcamentoResponse: Orçamento atualizado
        """
        try:
            # 1. Verificar se orçamento existe e permissões
            orcamento_atual = await self.repository.obter_orcamento_por_id(str(orcamento_id))
            
            if not orcamento_atual:
                raise Exception("Orçamento não encontrado")
            
            if not await self._verificar_permissao_orcamento(orcamento_atual, current_user):
                raise Exception("Sem permissão para editar este orçamento")
            
            # 2. Preparar dados de atualização apenas com campos não-nulos
            dados_atualizacao = {}
            recalcular_custos = False
            
            if orcamento_data.desconto_percentual is not None:
                dados_atualizacao['desconto_percentual'] = float(orcamento_data.desconto_percentual) / 100
                recalcular_custos = True
            
            if orcamento_data.medidor_selecionado_id:
                dados_atualizacao['medidor_selecionado_id'] = str(orcamento_data.medidor_selecionado_id)
                recalcular_custos = True
            
            if orcamento_data.montador_selecionado_id:
                dados_atualizacao['montador_selecionado_id'] = str(orcamento_data.montador_selecionado_id)
                recalcular_custos = True
            
            if orcamento_data.transportadora_selecionada_id:
                dados_atualizacao['transportadora_selecionada_id'] = str(orcamento_data.transportadora_selecionada_id)
                recalcular_custos = True
            
            if orcamento_data.plano_pagamento:
                dados_atualizacao['plano_pagamento'] = json.dumps([p.dict() for p in orcamento_data.plano_pagamento])
            
            if orcamento_data.observacoes is not None:
                dados_atualizacao['observacoes'] = orcamento_data.observacoes
            
            # 3. Recalcular custos se necessário
            if recalcular_custos:
                valor_final = float(orcamento_atual['valor_ambientes']) * (1 - dados_atualizacao.get('desconto_percentual', float(orcamento_atual['desconto_percentual'])))
                
                dados_calculo = {
                    'loja_id': orcamento_atual['loja_id'],
                    'vendedor_id': orcamento_atual['vendedor_id'],
                    'valor_ambientes': float(orcamento_atual['valor_ambientes']),
                    'valor_final': valor_final,
                    'custos_adicionais': orcamento_data.custos_adicionais or [],
                    'montador_id': dados_atualizacao.get('montador_selecionado_id', orcamento_atual['montador_selecionado_id']),
                    'medidor_id': dados_atualizacao.get('medidor_selecionado_id', orcamento_atual['medidor_selecionado_id']),
                    'transportadora_id': dados_atualizacao.get('transportadora_selecionada_id', orcamento_atual['transportadora_selecionada_id'])
                }
                
                calculo = await self.calcular_orcamento_completo(dados_calculo)
                
                dados_atualizacao.update({
                    'valor_final': valor_final,
                    'custo_fabrica': calculo['custos']['custo_fabrica'],
                    'comissao_vendedor': calculo['custos']['comissao_vendedor'],
                    'comissao_gerente': calculo['custos']['comissao_gerente'],
                    'custo_medidor': calculo['custos']['custo_medidor'],
                    'custo_montador': calculo['custos']['custo_montador'],
                    'custo_frete': calculo['custos']['custo_frete'],
                    'margem_lucro': calculo['margem_lucro']
                })
            
            # 4. Atualizar no banco
            orcamento_atualizado = await self.repository.atualizar_orcamento(str(orcamento_id), dados_atualizacao)
            
            # 5. Atualizar custos adicionais se fornecidos
            if orcamento_data.custos_adicionais is not None:
                await self.repository.atualizar_custos_adicionais(str(orcamento_id), orcamento_data.custos_adicionais)
            
            logger.info(f"Orçamento {orcamento_id} atualizado com sucesso")
            
            return await self._format_orcamento_response(orcamento_atualizado, current_user)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar orçamento: {str(e)}")
    
    async def excluir_orcamento(self, orcamento_id: uuid.UUID, current_user: Dict[str, Any]):
        """
        Exclui um orçamento (soft delete)
        
        Args:
            orcamento_id: ID do orçamento
            current_user: Usuário autenticado
        """
        try:
            orcamento = await self.repository.obter_orcamento_por_id(str(orcamento_id))
            
            if not orcamento:
                raise Exception("Orçamento não encontrado")
            
            if not await self._verificar_permissao_orcamento(orcamento, current_user):
                raise Exception("Sem permissão para excluir este orçamento")
            
            # Verificar se pode ser excluído (apenas em status negociação)
            if orcamento.get('status_nome', '').upper() not in ['NEGOCIACAO', 'NEGOCIAÇÃO']:
                raise Exception("Apenas orçamentos em negociação podem ser excluídos")
            
            await self.repository.excluir_orcamento(str(orcamento_id))
            
            logger.info(f"Orçamento {orcamento_id} excluído com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao excluir orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao excluir orçamento: {str(e)}")
    
    async def solicitar_aprovacao(self, orcamento_id: uuid.UUID, solicitacao: SolicitacaoAprovacao, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solicita aprovação para desconto
        
        Args:
            orcamento_id: ID do orçamento
            solicitacao: Dados da solicitação
            current_user: Usuário autenticado
            
        Returns:
            Dict: Resultado da solicitação
        """
        try:
            orcamento = await self.repository.obter_orcamento_por_id(str(orcamento_id))
            
            if not orcamento:
                raise Exception("Orçamento não encontrado")
            
            # Validar desconto solicitado
            desconto_decimal = float(solicitacao.desconto_solicitado) / 100
            validacao = await self.validar_limite_desconto(orcamento['loja_id'], current_user['user_id'], desconto_decimal)
            
            if not validacao['necessita_aprovacao']:
                raise Exception("Este desconto pode ser aplicado diretamente")
            
            # Registrar solicitação de aprovação
            aprovacao_id = await self.repository.criar_solicitacao_aprovacao({
                'orcamento_id': str(orcamento_id),
                'solicitante_id': current_user['user_id'],
                'desconto_solicitado': desconto_decimal,
                'justificativa': solicitacao.justificativa,
                'nivel_aprovacao': validacao['nivel_aprovacao_necessario']
            })
            
            logger.info(f"Solicitação de aprovação criada para orçamento {orcamento_id}")
            
            return {
                'aprovacao_id': aprovacao_id,
                'nivel_aprovacao': validacao['nivel_aprovacao_necessario'],
                'desconto_solicitado': solicitacao.desconto_solicitado,
                'status': 'AGUARDANDO_APROVACAO'
            }
            
        except Exception as e:
            logger.error(f"Erro ao solicitar aprovação para orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao solicitar aprovação: {str(e)}")
    
    async def processar_aprovacao(self, orcamento_id: uuid.UUID, aprovado: bool, justificativa: Optional[str], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma solicitação de aprovação
        
        Args:
            orcamento_id: ID do orçamento
            aprovado: True para aprovar, False para rejeitar
            justificativa: Justificativa da decisão
            current_user: Usuário autenticado (aprovador)
            
        Returns:
            Dict: Resultado da aprovação
        """
        try:
            # Implementar lógica de aprovação
            # TODO: Implementar verificação de hierarquia de aprovação
            
            resultado = await self.repository.processar_aprovacao(str(orcamento_id), {
                'aprovador_id': current_user['user_id'],
                'aprovado': aprovado,
                'justificativa': justificativa,
                'acao': 'APROVADO' if aprovado else 'REJEITADO'
            })
            
            logger.info(f"Aprovação processada para orçamento {orcamento_id}: {'APROVADO' if aprovado else 'REJEITADO'}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao processar aprovação para orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao processar aprovação: {str(e)}")
    
    # ===== MÉTODOS AUXILIARES =====
    
    async def _verificar_permissao_orcamento(self, orcamento: Dict[str, Any], current_user: Dict[str, Any]) -> bool:
        """
        Verifica se usuário tem permissão para acessar o orçamento
        
        Args:
            orcamento: Dados do orçamento
            current_user: Usuário autenticado
            
        Returns:
            bool: True se tem permissão
        """
        try:
            # Admin Master vê tudo
            if current_user['perfil'] == 'ADMIN_MASTER':
                return True
            
            # Verificar se é da mesma loja
            if orcamento['loja_id'] != current_user['loja_id']:
                return False
            
            # Vendedor só vê seus próprios
            if current_user['perfil'] == 'VENDEDOR':
                return orcamento['vendedor_id'] == current_user['user_id']
            
            # Gerente vê todos da loja
            if current_user['perfil'] == 'GERENTE':
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar permissão: {str(e)}")
            return False
    
    async def _format_orcamento_response(self, orcamento: Dict[str, Any], current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Formata resposta do orçamento baseado no perfil do usuário
        
        Args:
            orcamento: Dados do orçamento
            current_user: Usuário autenticado
            
        Returns:
            OrcamentoResponse: Resposta formatada
        """
        try:
            # Buscar dados relacionados
            ambientes = await self.repository.obter_ambientes_orcamento(orcamento['id'])
            custos_adicionais = await self.repository.obter_custos_adicionais(orcamento['id'])
            
            # Montar resumo financeiro baseado no perfil
            resumo_financeiro = {
                'valor_ambientes': orcamento['valor_ambientes'],
                'desconto_aplicado': orcamento['valor_ambientes'] * orcamento['desconto_percentual'],
                'valor_final': orcamento['valor_final']
            }
            
            # Admin Master vê custos detalhados
            if current_user['perfil'] == 'ADMIN_MASTER':
                resumo_financeiro.update({
                    'custo_fabrica': orcamento.get('custo_fabrica'),
                    'comissao_vendedor': orcamento.get('comissao_vendedor'),
                    'comissao_gerente': orcamento.get('comissao_gerente'),
                    'custo_medidor': orcamento.get('custo_medidor'),
                    'custo_montador': orcamento.get('custo_montador'),
                    'custo_frete': orcamento.get('custo_frete'),
                    'total_custos_adicionais': sum(c.get('valor_custo', 0) for c in custos_adicionais),
                    'margem_lucro': orcamento.get('margem_lucro')
                })
            
            return OrcamentoResponse(
                id=orcamento['id'],
                numero=orcamento['numero'],
                cliente_id=orcamento['cliente_id'],
                loja_id=orcamento['loja_id'],
                vendedor_id=orcamento['vendedor_id'],
                status_id=orcamento.get('status_id'),
                resumo_financeiro=resumo_financeiro,
                ambientes=ambientes,
                custos_adicionais=custos_adicionais,
                plano_pagamento=json.loads(orcamento.get('plano_pagamento', '[]')),
                necessita_aprovacao=orcamento.get('necessita_aprovacao', False),
                aprovador_id=orcamento.get('aprovador_id'),
                observacoes=orcamento.get('observacoes'),
                created_at=orcamento['created_at'],
                updated_at=orcamento['updated_at']
            )
            
        except Exception as e:
            logger.error(f"Erro ao formatar resposta do orçamento: {str(e)}")
            raise Exception(f"Erro ao formatar resposta: {str(e)}")
