import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from supabase import create_client, Client

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
