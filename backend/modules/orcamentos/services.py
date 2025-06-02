# Business logic helpers for orcamentos

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from decimal import Decimal
from datetime import datetime
import uuid

from .repository import OrcamentoRepository
from .schemas import OrcamentoCreate, OrcamentoUpdate, OrcamentoResponse, OrcamentoListItem, OrcamentoFilters

# Configurar logger
logger = logging.getLogger(__name__)


class OrcamentoService:
    """
    Service layer para orçamentos - orquestra cálculos completos
    Stack: FastAPI + Python + Pandas (conforme PRD.md)
    
    Responsabilidade: Lógica de negócio, cálculos, validações
    """
    
    def __init__(self, supabase_client):
        self.repository = OrcamentoRepository(supabase_client)
        self.supabase = supabase_client
    
    # ===== MÉTODOS CRUD BÁSICOS (conectar com Controllers) =====

    async def criar_orcamento(self, orcamento_data: OrcamentoCreate, current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Cria um novo orçamento com cálculos automáticos e validações
        
        Args:
            orcamento_data: Dados do orçamento vindos do Controller
            current_user: Usuário logado (contém loja_id)
            
        Returns:
            OrcamentoResponse: Orçamento criado com todos os cálculos
        """
        try:
            loja_id = current_user['loja_id']
            vendedor_id = current_user['id']
            
            logger.info(f"Criando orçamento para cliente {orcamento_data.cliente_id} na loja {loja_id}")
            
            # 1. Buscar ambientes e calcular valor base
            valor_ambientes = await self._calcular_valor_ambientes(orcamento_data.ambiente_ids, loja_id)
            
            # 2. Calcular valor final com desconto
            desconto_decimal = float(orcamento_data.desconto_percentual) / 100
            valor_final = valor_ambientes * (1 - desconto_decimal)
            
            # 3. Preparar dados para cálculo completo
            dados_calculo = {
                'loja_id': loja_id,
                'vendedor_id': vendedor_id,
                'valor_ambientes': valor_ambientes,
                'desconto_percentual': desconto_decimal,
                'custos_adicionais': [dict(item) for item in orcamento_data.custos_adicionais] if orcamento_data.custos_adicionais else []
            }
            
            # 4. Calcular orçamento completo
            calculo_completo = await self.criar_orcamento_completo(dados_calculo)
            
            # 5. Gerar numeração automática
            numero = await self._gerar_numero_orcamento(loja_id)
            
            # 6. Buscar status padrão
            status_padrao = await self._get_status_padrao(loja_id)
            
            # 7. Preparar dados para inserção
            orcamento_db = {
                'numero': numero,
                'cliente_id': str(orcamento_data.cliente_id),
                'loja_id': loja_id,
                'vendedor_id': vendedor_id,
                'medidor_selecionado_id': str(orcamento_data.medidor_selecionado_id),
                'montador_selecionado_id': str(orcamento_data.montador_selecionado_id),
                'transportadora_selecionada_id': str(orcamento_data.transportadora_selecionada_id),
                'valor_ambientes': valor_ambientes,
                'desconto_percentual': desconto_decimal,
                'valor_final': calculo_completo['valor_final'],
                'custo_fabrica': calculo_completo['custos']['custo_fabrica'],
                'comissao_vendedor': calculo_completo['custos']['comissao_vendedor'],
                'comissao_gerente': calculo_completo['custos']['comissao_gerente'],
                'custo_medidor': calculo_completo['custos']['custo_medidor'],
                'custo_montador': calculo_completo['custos']['custo_montador'],
                'custo_frete': calculo_completo['custos']['custo_frete'],
                'margem_lucro': calculo_completo['margem_lucro'],
                'config_snapshot': calculo_completo.get('config_snapshot', {}),
                'plano_pagamento': [dict(item) for item in orcamento_data.plano_pagamento],
                'necessita_aprovacao': calculo_completo['necessita_aprovacao'],
                'status_id': status_padrao['id'],
                'observacoes': orcamento_data.observacoes
            }
            
            # 8. Inserir orçamento
            orcamento_result = (
                self.supabase
                .table('c_orcamentos')
                .insert(orcamento_db)
                .execute()
            )
            
            if not orcamento_result.data:
                raise Exception("Erro ao inserir orçamento")
                
            orcamento_criado = orcamento_result.data[0]
            orcamento_id = orcamento_criado['id']
            
            # 9. Inserir relacionamentos com ambientes
            await self._inserir_ambientes_orcamento(orcamento_id, orcamento_data.ambiente_ids)
            
            # 10. Inserir custos adicionais se existirem
            if orcamento_data.custos_adicionais:
                await self._inserir_custos_adicionais(orcamento_id, orcamento_data.custos_adicionais)
            
            logger.info(f"Orçamento {numero} criado com sucesso: R$ {valor_final:,.2f}")
            
            # 11. Retornar orçamento completo
            return await self.obter_orcamento(orcamento_id, current_user)
            
        except Exception as e:
            logger.error(f"Erro ao criar orçamento: {str(e)}")
            raise Exception(f"Erro ao criar orçamento: {str(e)}")

    async def listar_orcamentos(self, filters: OrcamentoFilters, current_user: Dict[str, Any], skip: int = 0, limit: int = 50) -> List[OrcamentoListItem]:
        """
        Lista orçamentos com filtros aplicados e respeitando permissões
        
        Args:
            filters: Filtros aplicados
            current_user: Usuário logado 
            skip: Paginação - registros a pular
            limit: Paginação - limite de registros
            
        Returns:
            List[OrcamentoListItem]: Lista de orçamentos
        """
        try:
            loja_id = current_user['loja_id']
            perfil = current_user['perfil']
            user_id = current_user['id']
            
            # Construir query base
            query = (
                self.supabase
                .table('c_orcamentos')
                .select('''
                    id,
                    numero,
                    valor_final,
                    necessita_aprovacao,
                    created_at,
                    c_clientes!inner(nome),
                    config_status_orcamento!inner(nome_status),
                    cad_equipe!inner(nome)
                ''')
                .eq('loja_id', loja_id)
            )
            
            # Aplicar filtro por perfil
            if perfil == 'VENDEDOR':
                query = query.eq('vendedor_id', user_id)
            # GERENTE e ADMIN_MASTER veem todos da loja
            
            # Aplicar filtros opcionais
            if filters.vendedor_id:
                query = query.eq('vendedor_id', str(filters.vendedor_id))
            
            if filters.status_id:
                query = query.eq('status_id', str(filters.status_id))
                
            if filters.necessita_aprovacao is not None:
                query = query.eq('necessita_aprovacao', filters.necessita_aprovacao)
                
            if filters.valor_minimo:
                query = query.gte('valor_final', float(filters.valor_minimo))
                
            if filters.valor_maximo:
                query = query.lte('valor_final', float(filters.valor_maximo))
            
            # Executar query com paginação
            result = (
                query
                .order('created_at', desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )
            
            # Converter para OrcamentoListItem
            orcamentos = []
            for item in result.data:
                orcamento_item = OrcamentoListItem(
                    id=item['id'],
                    numero=item['numero'],
                    cliente_nome=item['c_clientes']['nome'],
                    valor_final=item['valor_final'],
                    status_nome=item['config_status_orcamento']['nome_status'],
                    necessita_aprovacao=item['necessita_aprovacao'],
                    vendedor_nome=item['cad_equipe']['nome'],
                    created_at=item['created_at']
                )
                orcamentos.append(orcamento_item)
            
            logger.debug(f"Listados {len(orcamentos)} orçamentos para {perfil} na loja {loja_id}")
            return orcamentos
            
        except Exception as e:
            logger.error(f"Erro ao listar orçamentos: {str(e)}")
            raise Exception(f"Erro ao listar orçamentos: {str(e)}")

    async def obter_orcamento(self, orcamento_id: str, current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Obtém orçamento por ID com dados adaptados ao perfil do usuário
        
        Args:
            orcamento_id: ID do orçamento
            current_user: Usuário logado
            
        Returns:
            OrcamentoResponse: Orçamento completo
        """
        try:
            loja_id = current_user['loja_id']
            perfil = current_user['perfil']
            
            # Buscar orçamento base
            result = (
                self.supabase
                .table('c_orcamentos')
                .select('*')
                .eq('id', orcamento_id)
                .eq('loja_id', loja_id)  # RLS: só da mesma loja
                .execute()
            )
            
            if not result.data:
                raise Exception("Orçamento não encontrado")
                
            orcamento = result.data[0]
            
            # Verificar permissão por perfil
            if perfil == 'VENDEDOR' and orcamento['vendedor_id'] != current_user['id']:
                raise Exception("Acesso negado: vendedor só vê próprios orçamentos")
            
            # Buscar ambientes relacionados
            ambientes = await self._get_ambientes_orcamento(orcamento_id)
            
            # Buscar custos adicionais
            custos_adicionais = await self._get_custos_adicionais_orcamento(orcamento_id)
            
            # Montar resumo financeiro (dados sensíveis apenas para Admin Master)
            resumo_financeiro = {
                'valor_ambientes': orcamento['valor_ambientes'],
                'desconto_aplicado': orcamento['valor_ambientes'] * orcamento['desconto_percentual'],
                'valor_final': orcamento['valor_final']
            }
            
            # Admin Master vê custos e margem
            if perfil == 'ADMIN_MASTER':
                resumo_financeiro.update({
                    'custo_fabrica': orcamento['custo_fabrica'],
                    'comissao_vendedor': orcamento['comissao_vendedor'],
                    'comissao_gerente': orcamento['comissao_gerente'],
                    'custo_medidor': orcamento['custo_medidor'],
                    'custo_montador': orcamento['custo_montador'],
                    'custo_frete': orcamento['custo_frete'],
                    'total_custos_adicionais': sum(c['valor_custo'] for c in custos_adicionais),
                    'margem_lucro': orcamento['margem_lucro']
                })
            
            # Montar response
            orcamento_response = OrcamentoResponse(
                id=orcamento['id'],
                numero=orcamento['numero'],
                cliente_id=orcamento['cliente_id'],
                loja_id=orcamento['loja_id'],
                vendedor_id=orcamento['vendedor_id'],
                status_id=orcamento['status_id'],
                resumo_financeiro=resumo_financeiro,
                ambientes=ambientes,
                custos_adicionais=custos_adicionais,
                plano_pagamento=orcamento['plano_pagamento'],
                necessita_aprovacao=orcamento['necessita_aprovacao'],
                aprovador_id=orcamento.get('aprovador_id'),
                observacoes=orcamento.get('observacoes'),
                created_at=orcamento['created_at'],
                updated_at=orcamento['updated_at']
            )
            
            return orcamento_response
            
        except Exception as e:
            logger.error(f"Erro ao obter orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao obter orçamento: {str(e)}")

    async def atualizar_orcamento(self, orcamento_id: str, orcamento_data: OrcamentoUpdate, current_user: Dict[str, Any]) -> OrcamentoResponse:
        """
        Atualiza orçamento existente com recálculos automáticos
        
        Args:
            orcamento_id: ID do orçamento
            orcamento_data: Dados de atualização
            current_user: Usuário logado
            
        Returns:
            OrcamentoResponse: Orçamento atualizado
        """
        try:
            # Verificar se orçamento existe e usuário tem permissão
            orcamento_atual = await self.obter_orcamento(orcamento_id, current_user)
            
            # Preparar dados de atualização
            dados_atualizacao = {}
            
            # Se há mudança de desconto, recalcular tudo
            if orcamento_data.desconto_percentual is not None:
                novo_desconto = float(orcamento_data.desconto_percentual) / 100
                valor_ambientes = orcamento_atual.resumo_financeiro.valor_ambientes
                novo_valor_final = valor_ambientes * (1 - novo_desconto)
                
                # Recalcular todos os custos
                dados_calculo = {
                    'loja_id': current_user['loja_id'],
                    'vendedor_id': orcamento_atual.vendedor_id,
                    'valor_ambientes': valor_ambientes,
                    'desconto_percentual': novo_desconto,
                    'custos_adicionais': []  # TODO: carregar custos existentes se necessário
                }
                
                calculo_completo = await self.criar_orcamento_completo(dados_calculo)
                
                dados_atualizacao.update({
                    'desconto_percentual': novo_desconto,
                    'valor_final': calculo_completo['valor_final'],
                    'custo_fabrica': calculo_completo['custos']['custo_fabrica'],
                    'comissao_vendedor': calculo_completo['custos']['comissao_vendedor'],
                    'comissao_gerente': calculo_completo['custos']['comissao_gerente'],
                    'custo_frete': calculo_completo['custos']['custo_frete'],
                    'margem_lucro': calculo_completo['margem_lucro'],
                    'necessita_aprovacao': calculo_completo['necessita_aprovacao']
                })
            
            # Outras atualizações simples
            if orcamento_data.medidor_selecionado_id:
                dados_atualizacao['medidor_selecionado_id'] = str(orcamento_data.medidor_selecionado_id)
                
            if orcamento_data.montador_selecionado_id:
                dados_atualizacao['montador_selecionado_id'] = str(orcamento_data.montador_selecionado_id)
                
            if orcamento_data.transportadora_selecionada_id:
                dados_atualizacao['transportadora_selecionada_id'] = str(orcamento_data.transportadora_selecionada_id)
                
            if orcamento_data.plano_pagamento:
                dados_atualizacao['plano_pagamento'] = [dict(item) for item in orcamento_data.plano_pagamento]
                
            if orcamento_data.observacoes is not None:
                dados_atualizacao['observacoes'] = orcamento_data.observacoes
            
            # Executar atualização
            if dados_atualizacao:
                dados_atualizacao['updated_at'] = datetime.utcnow().isoformat()
                
                update_result = (
                    self.supabase
                    .table('c_orcamentos')
                    .update(dados_atualizacao)
                    .eq('id', orcamento_id)
                    .execute()
                )
                
                if not update_result.data:
                    raise Exception("Erro ao atualizar orçamento")
            
            logger.info(f"Orçamento {orcamento_id} atualizado com sucesso")
            
            # Retornar orçamento atualizado
            return await self.obter_orcamento(orcamento_id, current_user)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar orçamento: {str(e)}")

    async def excluir_orcamento(self, orcamento_id: str, current_user: Dict[str, Any]) -> bool:
        """
        Exclui orçamento (soft delete) com validações de permissão
        
        Args:
            orcamento_id: ID do orçamento
            current_user: Usuário logado
            
        Returns:
            bool: True se excluído com sucesso
        """
        try:
            # Verificar se orçamento existe e usuário tem permissão
            orcamento = await self.obter_orcamento(orcamento_id, current_user)
            
            # Verificar se pode ser excluído (apenas status Negociação)
            # TODO: implementar verificação de status quando necessário
            
            # Soft delete (marcar como excluído)
            delete_result = (
                self.supabase
                .table('c_orcamentos')
                .update({
                    'excluido': True,
                    'excluido_em': datetime.utcnow().isoformat(),
                    'excluido_por': current_user['id']
                })
                .eq('id', orcamento_id)
                .execute()
            )
            
            logger.info(f"Orçamento {orcamento_id} excluído com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao excluir orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao excluir orçamento: {str(e)}")

    # ===== MÉTODOS AUXILIARES =====

    async def _calcular_valor_ambientes(self, ambiente_ids: List[str], loja_id: str) -> float:
        """Calcula valor total dos ambientes selecionados"""
        try:
            result = (
                self.supabase
                .table('c_ambientes')
                .select('valor_total')
                .in_('id', [str(id) for id in ambiente_ids])
                .eq('loja_id', loja_id)
                .execute()
            )
            
            total = sum(float(item['valor_total']) for item in result.data)
            logger.debug(f"Valor total dos ambientes: R$ {total:,.2f}")
            return total
            
        except Exception as e:
            logger.error(f"Erro ao calcular valor dos ambientes: {str(e)}")
            raise

    async def _gerar_numero_orcamento(self, loja_id: str) -> str:
        """Gera numeração automática para orçamento"""
        try:
            # TODO: Implementar lógica de numeração automática baseada na config da loja
            # Por enquanto, gerar número simples
            import random
            numero = f"ORC-{random.randint(1000, 9999)}"
            logger.debug(f"Número gerado: {numero}")
            return numero
            
        except Exception as e:
            logger.error(f"Erro ao gerar número do orçamento: {str(e)}")
            raise

    async def _get_status_padrao(self, loja_id: str) -> Dict[str, Any]:
        """Busca status padrão da loja"""
        try:
            result = (
                self.supabase
                .table('config_status_orcamento')
                .select('*')
                .eq('loja_id', loja_id)
                .eq('is_default', True)
                .execute()
            )
            
            if result.data:
                return result.data[0]
            else:
                # Criar status padrão se não existir
                status_padrao = {
                    'nome_status': 'Negociação',
                    'ordem': 1,
                    'loja_id': loja_id,
                    'bloqueia_edicao': False,
                    'is_default': True,
                    'is_final': False
                }
                
                insert_result = (
                    self.supabase
                    .table('config_status_orcamento')
                    .insert(status_padrao)
                    .execute()
                )
                
                return insert_result.data[0]
                
        except Exception as e:
            logger.error(f"Erro ao buscar status padrão: {str(e)}")
            raise

    async def _inserir_ambientes_orcamento(self, orcamento_id: str, ambiente_ids: List[str]):
        """Insere relacionamentos entre orçamento e ambientes"""
        try:
            relacionamentos = [
                {
                    'orcamento_id': orcamento_id,
                    'ambiente_id': str(ambiente_id),
                    'incluido': True
                }
                for ambiente_id in ambiente_ids
            ]
            
            (
                self.supabase
                .table('c_orcamento_ambientes')
                .insert(relacionamentos)
                .execute()
            )
            
        except Exception as e:
            logger.error(f"Erro ao inserir ambientes do orçamento: {str(e)}")
            raise

    async def _inserir_custos_adicionais(self, orcamento_id: str, custos_adicionais: List):
        """Insere custos adicionais do orçamento"""
        try:
            custos_db = [
                {
                    'orcamento_id': orcamento_id,
                    'descricao_custo': custo.descricao_custo,
                    'valor_custo': float(custo.valor_custo)
                }
                for custo in custos_adicionais
            ]
            
            (
                self.supabase
                .table('c_orcamento_custos_adicionais')
                .insert(custos_db)
                .execute()
            )
            
        except Exception as e:
            logger.error(f"Erro ao inserir custos adicionais: {str(e)}")
            raise

    async def _get_ambientes_orcamento(self, orcamento_id: str) -> List[Dict]:
        """Busca ambientes relacionados ao orçamento"""
        try:
            result = (
                self.supabase
                .table('c_orcamento_ambientes')
                .select('''
                    c_ambientes!inner(
                        id,
                        nome_ambiente,
                        valor_total,
                        linha_produto
                    )
                ''')
                .eq('orcamento_id', orcamento_id)
                .eq('incluido', True)
                .execute()
            )
            
            ambientes = []
            for item in result.data:
                ambiente = item['c_ambientes']
                ambientes.append({
                    'id': ambiente['id'],
                    'nome_ambiente': ambiente['nome_ambiente'],
                    'valor_total': ambiente['valor_total'],
                    'linha_produto': ambiente['linha_produto']
                })
            
            return ambientes
            
        except Exception as e:
            logger.error(f"Erro ao buscar ambientes do orçamento: {str(e)}")
            return []

    async def _get_custos_adicionais_orcamento(self, orcamento_id: str) -> List[Dict]:
        """Busca custos adicionais do orçamento"""
        try:
            result = (
                self.supabase
                .table('c_orcamento_custos_adicionais')
                .select('*')
                .eq('orcamento_id', orcamento_id)
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error(f"Erro ao buscar custos adicionais: {str(e)}")
            return []

    # ===== MÉTODOS DE APROVAÇÃO (placeholder para conexão futura) =====

    async def solicitar_aprovacao(self, orcamento_id: str, solicitacao, current_user: Dict[str, Any]):
        """TODO: Implementar lógica de solicitação de aprovação"""
        return {"message": "Funcionalidade de aprovação em desenvolvimento"}

    async def processar_aprovacao(self, orcamento_id: str, aprovado: bool, justificativa: str, current_user: Dict[str, Any]):
        """TODO: Implementar lógica de processamento de aprovação"""
        return {"message": "Funcionalidade de aprovação em desenvolvimento"}

    async def calcular_custos(self, orcamento_id: str, current_user: Dict[str, Any]):
        """TODO: Implementar retorno de custos detalhados"""
        return {"message": "Funcionalidade de cálculo de custos em desenvolvimento"}

    async def duplicar_orcamento(self, orcamento_id: str, current_user: Dict[str, Any]):
        """TODO: Implementar duplicação de orçamento"""
        return {"message": "Funcionalidade de duplicação em desenvolvimento"}

    async def relatorio_margem(self, filtros, current_user: Dict[str, Any]):
        """TODO: Implementar relatório de margem"""
        return {"message": "Relatório de margem em desenvolvimento"}

    async def metricas_dashboard(self, periodo_dias: int, current_user: Dict[str, Any]):
        """TODO: Implementar métricas do dashboard"""
        return {"message": "Métricas do dashboard em desenvolvimento"}

    async def listar_status_disponiveis(self, current_user: Dict[str, Any]):
        """TODO: Implementar listagem de status disponíveis"""
        return {"message": "Listagem de status em desenvolvimento"}

    async def historico_aprovacoes(self, orcamento_id: str, current_user: Dict[str, Any]):
        """TODO: Implementar histórico de aprovações"""
        return {"message": "Histórico de aprovações em desenvolvimento"}

    
    # ===== ENGINE DE CÁLCULO (MANTIDO) =====
    
    def calcular_comissao_faixa_unica_pandas(self, valor_venda: float, regras_df: pd.DataFrame) -> Dict[str, Any]:
        """
        🚨 CORREÇÃO CRÍTICA: Engine de cálculo de comissão por FAIXA ÚNICA (não progressivo)
        
        REGRA REAL DE NEGÓCIO:
        - Identifica qual faixa o valor se encaixa
        - Aplica o percentual da faixa sobre TODO o valor
        - NÃO soma faixas anteriores (isso era o erro)
        
        Args:
            valor_venda (float): Valor da venda para calcular comissão
            regras_df (pd.DataFrame): DataFrame com regras de comissão por faixa
            
        Returns:
            Dict[str, Any]: Resultado do cálculo com detalhamento
            
        Exemplos corretos:
        - R$ 24.999 → Faixa 1 (até 25k) → 5% × R$ 24.999 = R$ 1.249,95
        - R$ 40.000 → Faixa 2 (25k-50k) → 6% × R$ 40.000 = R$ 2.400,00
        - R$ 100.000 → Faixa 3 (50k+) → 8% × R$ 100.000 = R$ 8.000,00
        """
        if regras_df.empty:
            logger.warning("DataFrame de regras vazio, retornando comissão zero")
            return {
                'comissao_total': 0.0,
                'detalhes_faixas': [],
                'valor_total_processado': valor_venda,
                'faixa_aplicada': None
            }
        
        logger.debug(f"🔧 CORREÇÃO: Cálculo por faixa única para valor: R$ {valor_venda:,.2f}")
        
        # Ordenar regras por valor mínimo para processar em ordem
        regras_ordenadas = regras_df.sort_values('valor_minimo')
        
        # Encontrar a faixa onde o valor se encaixa
        faixa_aplicada = None
        for idx, regra in regras_ordenadas.iterrows():
            valor_min = float(regra['valor_minimo'])
            valor_max = float(regra['valor_maximo']) if pd.notna(regra['valor_maximo']) else float('inf')
            
            # Verificar se valor está nesta faixa
            if valor_min <= valor_venda <= valor_max:
                faixa_aplicada = regra
                break
        
        if faixa_aplicada is None:
            logger.warning(f"Nenhuma faixa encontrada para valor R$ {valor_venda:,.2f}")
            return {
                'comissao_total': 0.0,
                'detalhes_faixas': [],
                'valor_total_processado': valor_venda,
                'faixa_aplicada': None
            }
        
        # Calcular comissão: percentual da faixa × valor total
        percentual_faixa = float(faixa_aplicada['percentual'])
        comissao_total = valor_venda * percentual_faixa
        
        # Detalhar para auditoria
        detalhe_faixa = {
            'faixa': int(faixa_aplicada['ordem']),
            'valor_minimo': float(faixa_aplicada['valor_minimo']),
            'valor_maximo': float(faixa_aplicada['valor_maximo']) if pd.notna(faixa_aplicada['valor_maximo']) else None,
            'percentual': percentual_faixa,
            'valor_total_aplicado': float(valor_venda),
            'comissao_calculada': float(comissao_total)
        }
        
        resultado = {
            'comissao_total': float(comissao_total),
            'detalhes_faixas': [detalhe_faixa],  # Sempre uma única faixa
            'valor_total_processado': float(valor_venda),
            'faixa_aplicada': int(faixa_aplicada['ordem'])
        }
        
        logger.info(f"✅ Faixa {faixa_aplicada['ordem']}: R$ {valor_venda:,.2f} × {percentual_faixa:.1%} = R$ {comissao_total:,.2f}")
        
        return resultado

    # Manter método antigo por compatibilidade, mas redirecionar para o correto
    def calcular_comissao_progressiva_pandas(self, valor_venda: float, regras_df: pd.DataFrame) -> Dict[str, Any]:
        """
        🚨 MÉTODO DEPRECIADO: Redirecionando para cálculo correto por faixa única
        
        AVISO: O nome "progressiva" estava incorreto. Comissão real é por faixa única.
        Este método mantido apenas para compatibilidade, mas chama o algoritmo correto.
        """
        logger.warning("⚠️ Método 'progressiva' depreciado. Usando cálculo correto por faixa única.")
        return self.calcular_comissao_faixa_unica_pandas(valor_venda, regras_df)

    def _valor_atingido_pela_faixa(self, valor_venda: float, valor_minimo: float, valor_maximo: Optional[float]) -> bool:
        """
        🚨 MÉTODO DEPRECIADO: Era usado no algoritmo progressivo incorreto
        
        Mantido apenas para compatibilidade. O novo algoritmo usa lógica mais simples.
        """
        valor_max_efetivo = valor_maximo if valor_maximo is not None and not pd.isna(valor_maximo) else float('inf')
        return valor_minimo <= valor_venda <= valor_max_efetivo
    
    def _calcular_valor_da_faixa(
        self, 
        valor_venda: float, 
        valor_minimo: float, 
        valor_maximo: Optional[float], 
        percentual: float
    ) -> tuple[float, float]:
        """
        🚨 MÉTODO DEPRECIADO: Era usado no algoritmo progressivo incorreto
        
        Novo algoritmo simplesmente aplica: valor_total × percentual_faixa
        """
        # Para compatibilidade, retornar como se fosse faixa única
        valor_max_efetivo = valor_maximo if valor_maximo is not None and not pd.isna(valor_maximo) else float('inf')
        
        if valor_minimo <= valor_venda <= valor_max_efetivo:
            # Valor se encaixa nesta faixa - aplicar sobre total
            return valor_venda, valor_venda * percentual
        else:
            # Valor não se encaixa nesta faixa
            return 0.0, 0.0

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
        comissao_vendedor_calc = self.calcular_comissao_faixa_unica_pandas(valor_final, regras_vendedor_df)
        custos_detalhes['comissao_vendedor'] = comissao_vendedor_calc['comissao_total']
        
        # 3. Comissão gerente (progressiva com Pandas) 
        regras_gerente_df = await self.repository.get_regras_comissao(loja_id, 'GERENTE')
        comissao_gerente_calc = self.calcular_comissao_faixa_unica_pandas(valor_final, regras_gerente_df)
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
        resultado = self.calcular_comissao_faixa_unica_pandas(valor_teste, regras_teste)
        
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
