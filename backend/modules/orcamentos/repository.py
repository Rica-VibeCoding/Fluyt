import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from supabase import create_client, Client
import uuid
from datetime import datetime

# Configurar logger
logger = logging.getLogger(__name__)


class OrcamentoRepository:
    """
    Repository para operações de orçamentos com Supabase - APENAS DADOS
    Stack: FastAPI + Python + Pandas (conforme PRD.md)
    
    Responsabilidade: Acesso a dados, queries, conversões para DataFrame
    Lógica de negócio/cálculos: OrcamentoService
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    # ===== MÉTODOS CRUD PARA SERVICE =====
    
    async def criar_orcamento(self, dados_orcamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria novo orçamento no banco de dados
        
        Args:
            dados_orcamento: Dados do orçamento para inserir
            
        Returns:
            Dict[str, Any]: Orçamento criado com ID e número gerado
        """
        try:
            # 1. Gerar numeração automática
            proximo_numero = await self._obter_proximo_numero(dados_orcamento['loja_id'])
            
            # 2. Buscar status padrão
            status_padrao = await self._obter_status_padrao(dados_orcamento['loja_id'])
            
            # 3. Preparar dados para inserção
            dados_insercao = {
                **dados_orcamento,
                'numero': proximo_numero,
                'status_id': status_padrao['id'] if status_padrao else None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 4. Inserir orçamento
            result = (
                self.supabase
                .table('c_orcamentos')
                .insert(dados_insercao)
                .execute()
            )
            
            if not result.data:
                raise Exception("Erro ao inserir orçamento")
            
            orcamento_criado = result.data[0]
            
            # 5. Atualizar próximo número na configuração
            await self._incrementar_proximo_numero(dados_orcamento['loja_id'])
            
            logger.info(f"Orçamento criado com ID {orcamento_criado['id']} e número {proximo_numero}")
            
            return orcamento_criado
            
        except Exception as e:
            logger.error(f"Erro ao criar orçamento: {str(e)}")
            raise Exception(f"Erro ao criar orçamento: {str(e)}")
    
    async def listar_orcamentos(self, filters: Any, loja_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lista orçamentos com filtros aplicados
        
        Args:
            filters: Filtros de busca
            loja_id: ID da loja para filtrar
            skip: Registros para pular
            limit: Limite de registros
            
        Returns:
            List[Dict[str, Any]]: Lista de orçamentos
        """
        try:
            # Construir query base com joins
            query = (
                self.supabase
                .table('c_orcamentos')
                .select('''
                    id,
                    numero,
                    valor_final,
                    necessita_aprovacao,
                    created_at,
                    c_clientes(nome),
                    config_status_orcamento(nome_status),
                    cad_equipe(nome)
                ''')
                .eq('loja_id', loja_id)
            )
            
            # Aplicar filtros se fornecidos
            if filters.cliente_nome:
                # Note: Esta query pode precisar ser ajustada dependendo do Supabase
                pass  # TODO: Implementar filtro por nome do cliente
            
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
            
            # Aplicar paginação e ordenação
            query = query.order('created_at', desc=True).range(skip, skip + limit - 1)
            
            result = query.execute()
            
            # Formatar resultado para compatibilidade
            orcamentos = []
            for orc in result.data:
                orcamento_formatado = {
                    'id': orc['id'],
                    'numero': orc['numero'],
                    'cliente_nome': orc['c_clientes']['nome'] if orc.get('c_clientes') else 'Cliente não encontrado',
                    'valor_final': orc['valor_final'],
                    'status_nome': orc['config_status_orcamento']['nome_status'] if orc.get('config_status_orcamento') else 'Sem status',
                    'necessita_aprovacao': orc['necessita_aprovacao'],
                    'vendedor_nome': orc['cad_equipe']['nome'] if orc.get('cad_equipe') else 'Vendedor não encontrado',
                    'created_at': orc['created_at']
                }
                orcamentos.append(orcamento_formatado)
            
            logger.debug(f"Listados {len(orcamentos)} orçamentos para loja {loja_id}")
            
            return orcamentos
            
        except Exception as e:
            logger.error(f"Erro ao listar orçamentos: {str(e)}")
            raise Exception(f"Erro ao listar orçamentos: {str(e)}")
    
    async def obter_orcamento_por_id(self, orcamento_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém orçamento por ID
        
        Args:
            orcamento_id: ID do orçamento
            
        Returns:
            Optional[Dict[str, Any]]: Dados do orçamento ou None se não encontrado
        """
        try:
            result = (
                self.supabase
                .table('c_orcamentos')
                .select('*')
                .eq('id', orcamento_id)
                .single()
                .execute()
            )
            
            if result.data:
                logger.debug(f"Orçamento {orcamento_id} encontrado")
                return result.data
            else:
                logger.warning(f"Orçamento {orcamento_id} não encontrado")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao obter orçamento: {str(e)}")
    
    async def atualizar_orcamento(self, orcamento_id: str, dados_atualizacao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza orçamento existente
        
        Args:
            orcamento_id: ID do orçamento
            dados_atualizacao: Dados para atualizar
            
        Returns:
            Dict[str, Any]: Orçamento atualizado
        """
        try:
            # Adicionar timestamp de atualização
            dados_atualizacao['updated_at'] = datetime.now().isoformat()
            
            result = (
                self.supabase
                .table('c_orcamentos')
                .update(dados_atualizacao)
                .eq('id', orcamento_id)
                .execute()
            )
            
            if not result.data:
                raise Exception("Orçamento não encontrado para atualização")
            
            logger.info(f"Orçamento {orcamento_id} atualizado com sucesso")
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Erro ao atualizar orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar orçamento: {str(e)}")
    
    async def excluir_orcamento(self, orcamento_id: str):
        """
        Exclui orçamento (soft delete - marca como inativo)
        
        Args:
            orcamento_id: ID do orçamento
        """
        try:
            # Soft delete - marcar como excluído
            result = (
                self.supabase
                .table('c_orcamentos')
                .update({
                    'ativo': False,
                    'deleted_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                .eq('id', orcamento_id)
                .execute()
            )
            
            if not result.data:
                raise Exception("Orçamento não encontrado para exclusão")
            
            logger.info(f"Orçamento {orcamento_id} excluído com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao excluir orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao excluir orçamento: {str(e)}")
    
    async def calcular_valor_total_ambientes(self, ambiente_ids: List[uuid.UUID]) -> float:
        """
        Calcula valor total dos ambientes selecionados
        
        Args:
            ambiente_ids: Lista de IDs dos ambientes
            
        Returns:
            float: Valor total dos ambientes
        """
        try:
            if not ambiente_ids:
                return 0.0
            
            # Converter UUIDs para strings
            ids_strings = [str(aid) for aid in ambiente_ids]
            
            result = (
                self.supabase
                .table('c_ambientes')
                .select('valor_total')
                .in_('id', ids_strings)
                .execute()
            )
            
            if not result.data:
                raise Exception("Nenhum ambiente encontrado")
            
            total = sum(float(amb['valor_total']) for amb in result.data)
            
            logger.debug(f"Valor total de {len(ambiente_ids)} ambientes: R$ {total:,.2f}")
            
            return total
            
        except Exception as e:
            logger.error(f"Erro ao calcular valor total dos ambientes: {str(e)}")
            raise Exception(f"Erro ao calcular valor dos ambientes: {str(e)}")
    
    async def salvar_orcamento_ambientes(self, orcamento_id: str, ambiente_ids: List[uuid.UUID]):
        """
        Salva relacionamento entre orçamento e ambientes
        
        Args:
            orcamento_id: ID do orçamento
            ambiente_ids: Lista de IDs dos ambientes
        """
        try:
            # Preparar dados para inserção
            relacionamentos = [
                {
                    'orcamento_id': orcamento_id,
                    'ambiente_id': str(aid),
                    'incluido': True
                }
                for aid in ambiente_ids
            ]
            
            result = (
                self.supabase
                .table('c_orcamento_ambientes')
                .insert(relacionamentos)
                .execute()
            )
            
            if not result.data:
                raise Exception("Erro ao salvar relacionamento orçamento-ambientes")
            
            logger.debug(f"Relacionamento orçamento-ambientes salvo: {len(ambiente_ids)} ambientes")
            
        except Exception as e:
            logger.error(f"Erro ao salvar relacionamento orçamento-ambientes: {str(e)}")
            raise Exception(f"Erro ao salvar ambientes do orçamento: {str(e)}")
    
    async def salvar_custos_adicionais(self, orcamento_id: str, custos_adicionais: List[Any]):
        """
        Salva custos adicionais do orçamento
        
        Args:
            orcamento_id: ID do orçamento
            custos_adicionais: Lista de custos adicionais
        """
        try:
            if not custos_adicionais:
                return
            
            # Preparar dados para inserção
            custos_para_inserir = [
                {
                    'orcamento_id': orcamento_id,
                    'descricao_custo': custo.descricao_custo,
                    'valor_custo': float(custo.valor_custo)
                }
                for custo in custos_adicionais
            ]
            
            result = (
                self.supabase
                .table('c_orcamento_custos_adicionais')
                .insert(custos_para_inserir)
                .execute()
            )
            
            if not result.data:
                raise Exception("Erro ao salvar custos adicionais")
            
            logger.debug(f"Custos adicionais salvos: {len(custos_adicionais)} itens")
            
        except Exception as e:
            logger.error(f"Erro ao salvar custos adicionais: {str(e)}")
            raise Exception(f"Erro ao salvar custos adicionais: {str(e)}")
    
    async def obter_ambientes_orcamento(self, orcamento_id: str) -> List[Dict[str, Any]]:
        """
        Obtém ambientes relacionados ao orçamento
        
        Args:
            orcamento_id: ID do orçamento
            
        Returns:
            List[Dict[str, Any]]: Lista de ambientes
        """
        try:
            result = (
                self.supabase
                .table('c_orcamento_ambientes')
                .select('''
                    c_ambientes(
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
                if item.get('c_ambientes'):
                    ambiente = item['c_ambientes']
                    ambientes.append({
                        'id': ambiente['id'],
                        'nome_ambiente': ambiente['nome_ambiente'],
                        'valor_total': ambiente['valor_total'],
                        'linha_produto': ambiente.get('linha_produto')
                    })
            
            logger.debug(f"Obtidos {len(ambientes)} ambientes para orçamento {orcamento_id}")
            
            return ambientes
            
        except Exception as e:
            logger.error(f"Erro ao obter ambientes do orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao obter ambientes: {str(e)}")
    
    async def obter_custos_adicionais(self, orcamento_id: str) -> List[Dict[str, Any]]:
        """
        Obtém custos adicionais do orçamento
        
        Args:
            orcamento_id: ID do orçamento
            
        Returns:
            List[Dict[str, Any]]: Lista de custos adicionais
        """
        try:
            result = (
                self.supabase
                .table('c_orcamento_custos_adicionais')
                .select('*')
                .eq('orcamento_id', orcamento_id)
                .execute()
            )
            
            custos = [
                {
                    'id': custo['id'],
                    'descricao_custo': custo['descricao_custo'],
                    'valor_custo': custo['valor_custo']
                }
                for custo in result.data
            ]
            
            logger.debug(f"Obtidos {len(custos)} custos adicionais para orçamento {orcamento_id}")
            
            return custos
            
        except Exception as e:
            logger.error(f"Erro ao obter custos adicionais do orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao obter custos adicionais: {str(e)}")
    
    async def atualizar_custos_adicionais(self, orcamento_id: str, custos_adicionais: List[Any]):
        """
        Atualiza custos adicionais do orçamento (remove todos e insere novos)
        
        Args:
            orcamento_id: ID do orçamento
            custos_adicionais: Lista de custos adicionais
        """
        try:
            # 1. Remover custos existentes
            self.supabase.table('c_orcamento_custos_adicionais').delete().eq('orcamento_id', orcamento_id).execute()
            
            # 2. Inserir novos custos (se existirem)
            if custos_adicionais:
                await self.salvar_custos_adicionais(orcamento_id, custos_adicionais)
            
            logger.debug(f"Custos adicionais atualizados para orçamento {orcamento_id}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar custos adicionais do orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar custos adicionais: {str(e)}")
    
    async def criar_solicitacao_aprovacao(self, dados_aprovacao: Dict[str, Any]) -> str:
        """
        Cria solicitação de aprovação
        
        Args:
            dados_aprovacao: Dados da solicitação
            
        Returns:
            str: ID da aprovação criada
        """
        try:
            result = (
                self.supabase
                .table('c_aprovacao_historico')
                .insert({
                    **dados_aprovacao,
                    'acao': 'SOLICITADO',
                    'created_at': datetime.now().isoformat()
                })
                .execute()
            )
            
            if not result.data:
                raise Exception("Erro ao criar solicitação de aprovação")
            
            aprovacao_id = result.data[0]['id']
            
            logger.info(f"Solicitação de aprovação criada com ID {aprovacao_id}")
            
            return aprovacao_id
            
        except Exception as e:
            logger.error(f"Erro ao criar solicitação de aprovação: {str(e)}")
            raise Exception(f"Erro ao criar solicitação de aprovação: {str(e)}")
    
    async def processar_aprovacao(self, orcamento_id: str, dados_processamento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa aprovação de orçamento
        
        Args:
            orcamento_id: ID do orçamento
            dados_processamento: Dados do processamento
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        try:
            # 1. Atualizar histórico de aprovação
            result = (
                self.supabase
                .table('c_aprovacao_historico')
                .insert({
                    'orcamento_id': orcamento_id,
                    **dados_processamento,
                    'created_at': datetime.now().isoformat()
                })
                .execute()
            )
            
            # 2. Atualizar status do orçamento se aprovado
            if dados_processamento.get('aprovado'):
                self.supabase.table('c_orcamentos').update({
                    'necessita_aprovacao': False,
                    'aprovador_id': dados_processamento['aprovador_id'],
                    'updated_at': datetime.now().isoformat()
                }).eq('id', orcamento_id).execute()
            
            logger.info(f"Aprovação processada para orçamento {orcamento_id}")
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Erro ao processar aprovação para orçamento {orcamento_id}: {str(e)}")
            raise Exception(f"Erro ao processar aprovação: {str(e)}")
    
    # ===== MÉTODOS AUXILIARES =====
    
    async def _obter_proximo_numero(self, loja_id: str) -> str:
        """
        Obtém próximo número de orçamento para a loja
        
        Args:
            loja_id: ID da loja
            
        Returns:
            str: Próximo número formatado
        """
        try:
            config = await self.get_config_loja(loja_id)
            
            proximo_numero = config.get('proximo_numero_orcamento', 1)
            prefixo = config.get('prefixo_numeracao', '')
            formato = config.get('formato_numeracao', 'SEQUENCIAL')
            
            # Formatar número baseado na configuração
            if formato == 'SEQUENCIAL':
                numero_formatado = f"{prefixo}{proximo_numero}"
            elif formato == 'ANO_SEQUENCIAL':
                ano_atual = datetime.now().year
                numero_formatado = f"{prefixo}{ano_atual}-{proximo_numero:04d}"
            else:  # PERSONALIZADO
                numero_formatado = f"{prefixo}{proximo_numero}"
            
            logger.debug(f"Próximo número gerado para loja {loja_id}: {numero_formatado}")
            
            return numero_formatado
            
        except Exception as e:
            logger.error(f"Erro ao obter próximo número para loja {loja_id}: {str(e)}")
            raise Exception(f"Erro ao gerar numeração: {str(e)}")
    
    async def _incrementar_proximo_numero(self, loja_id: str):
        """
        Incrementa próximo número na configuração da loja
        
        Args:
            loja_id: ID da loja
        """
        try:
            config_atual = await self.get_config_loja(loja_id)
            novo_numero = config_atual.get('proximo_numero_orcamento', 1) + 1
            
            self.supabase.table('config_loja').update({
                'proximo_numero_orcamento': novo_numero
            }).eq('loja_id', loja_id).execute()
            
            logger.debug(f"Próximo número incrementado para {novo_numero} na loja {loja_id}")
            
        except Exception as e:
            logger.error(f"Erro ao incrementar próximo número para loja {loja_id}: {str(e)}")
            # Não levantar exceção aqui para não quebrar criação do orçamento
            pass
    
    async def _obter_status_padrao(self, loja_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status padrão da loja
        
        Args:
            loja_id: ID da loja
            
        Returns:
            Optional[Dict[str, Any]]: Status padrão ou None
        """
        try:
            result = (
                self.supabase
                .table('config_status_orcamento')
                .select('*')
                .eq('loja_id', loja_id)
                .eq('is_default', True)
                .single()
                .execute()
            )
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.warning(f"Status padrão não encontrado para loja {loja_id}: {str(e)}")
            return None

    # ===== MÉTODOS EXISTENTES MANTIDOS =====
    
    async def get_regras_comissao(self, loja_id: str, tipo: str) -> pd.DataFrame:
        """
        Busca regras de comissão progressiva e retorna como DataFrame para cálculos com Pandas
        
        Args:
            loja_id (str): ID da loja
            tipo (str): Tipo de comissão ('VENDEDOR' ou 'GERENTE')
            
        Returns:
            pd.DataFrame: DataFrame com regras ordenadas por faixa, pronto para cálculos
            
        Raises:
            Exception: Em caso de erro na consulta
            
        Colunas do DataFrame retornado:
        - id, loja_id, tipo_comissao, valor_minimo, valor_maximo, percentual, ordem
        """
        try:
            # Query Supabase com filtros e ordenação
            result = (
                self.supabase
                .table('config_regras_comissao_faixa')
                .select('*')
                .eq('loja_id', loja_id)
                .eq('tipo_comissao', tipo)
                .order('ordem')
                .execute()
            )
            
            if result.data:
                # Converter para DataFrame Pandas (conforme stack documentado)
                df = pd.DataFrame(result.data)
                
                # Garantir tipos corretos para cálculos
                df['valor_minimo'] = pd.to_numeric(df['valor_minimo'], errors='coerce')
                df['valor_maximo'] = pd.to_numeric(df['valor_maximo'], errors='coerce') 
                df['percentual'] = pd.to_numeric(df['percentual'], errors='coerce')
                df['ordem'] = pd.to_numeric(df['ordem'], errors='coerce')
                
                # Ordenar por ordem para garantir sequência correta
                df = df.sort_values('ordem').reset_index(drop=True)
                
                logger.debug(f"Regras de comissão carregadas: {len(df)} faixas para {tipo} na loja {loja_id}")
                return df
            else:
                logger.warning(f"Nenhuma regra de comissão encontrada para loja {loja_id}, tipo {tipo}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Erro ao buscar regras de comissão para loja {loja_id}, tipo {tipo}: {str(e)}")
            raise Exception(f"Erro ao buscar regras de comissão: {str(e)}")

    async def get_config_loja(self, loja_id: str) -> Dict[str, Any]:
        """
        Busca configurações de uma loja. Se não existir, cria automaticamente com valores padrão.
        Mantido como Dict para compatibilidade, mas preparado para uso com Pandas.
        
        Args:
            loja_id (str): ID da loja
            
        Returns:
            Dict[str, Any]: Configurações da loja (sempre válidas)
            
        Raises:
            Exception: Em caso de erro na consulta/criação
        """
        try:
            # Tentar buscar configuração existente
            result = (
                self.supabase
                .table('config_loja')
                .select('*')
                .eq('loja_id', loja_id)
                .execute()
            )
            
            if result.data:
                logger.debug(f"Config encontrada para loja {loja_id}")
                return result.data[0]
            else:
                # Config não existe - criar automaticamente com valores padrão
                logger.info(f"Config não encontrada para loja {loja_id}, criando automaticamente")
                return await self._criar_config_padrao(loja_id)
                
        except Exception as e:
            logger.error(f"Erro ao buscar/criar configuração da loja {loja_id}: {str(e)}")
            raise Exception(f"Erro ao buscar/criar configuração da loja: {str(e)}")

    async def _criar_config_padrao(self, loja_id: str) -> Dict[str, Any]:
        """
        Cria configuração padrão para uma loja com tratamento de concorrência
        Valores otimizados para uso com Pandas nos cálculos.
        """
        try:
            # Configuração padrão conforme schema (tipos compatíveis com Pandas)
            config_padrao = {
                'loja_id': loja_id,
                'deflator_custo_fabrica': 0.40,        # 40% sobre valor XML
                'valor_medidor_padrao': 200.00,        # R$ 200 fixo
                'valor_frete_percentual': 0.02,        # 2% sobre valor venda
                'limite_desconto_vendedor': 0.15,      # 15% limite vendedor
                'limite_desconto_gerente': 0.25,       # 25% limite gerente
                'numero_inicial_orcamento': 1,         # Número inicial
                'proximo_numero_orcamento': 1,         # Próximo número
                'formato_numeracao': 'SEQUENCIAL',     # Enum como string
                'prefixo_numeracao': ''                # Sem prefixo padrão
            }
            
            # Tentar inserir (pode falhar se outro processo criou simultaneamente)
            try:
                insert_result = (
                    self.supabase
                    .table('config_loja')
                    .insert(config_padrao)
                    .execute()
                )
                
                logger.info(f"Config padrão criada para loja {loja_id}")
                return insert_result.data[0]
                
            except Exception as insert_error:
                # Se falhou na inserção, pode ser concorrência - tentar buscar novamente
                logger.warning(f"Falha na inserção (provável concorrência), tentando buscar novamente: {str(insert_error)}")
                
                result = (
                    self.supabase
                    .table('config_loja')
                    .select('*')
                    .eq('loja_id', loja_id)
                    .execute()
                )
                
                if result.data:
                    logger.info(f"Config encontrada após tentativa de criação (concorrência resolvida)")
                    return result.data[0]
                else:
                    # Se ainda assim não existe, é erro real
                    raise Exception("Erro na criação da configuração padrão")
                    
        except Exception as e:
            logger.error(f"Erro ao criar configuração padrão para loja {loja_id}: {str(e)}")
            raise Exception(f"Erro ao criar configuração padrão: {str(e)}")


# Função auxiliar para compatibilidade com código existente
async def repo_list_orcamentos():
    """Função legacy - TODO: migrar para OrcamentoRepository.list_orcamentos()"""
    # TODO: call Supabase HTTP API
    return []
