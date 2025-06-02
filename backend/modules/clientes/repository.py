"""
Repository para operações de clientes com Supabase.
Responsabilidade: Acesso a dados, queries, conversões.
"""

import logging
from typing import List, Dict, Any, Optional
from supabase import Client
from .schemas import ClienteFilters

# Configurar logger
logger = logging.getLogger(__name__)


class ClienteRepository:
    """
    Repository para operações de clientes com Supabase - APENAS DADOS
    
    Responsabilidade: Acesso a dados, queries
    Lógica de negócio: ClienteService
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def criar_cliente(self, dados_cliente: Dict[str, Any], loja_id: str) -> Dict[str, Any]:
        """
        Cria um novo cliente no banco de dados
        
        Args:
            dados_cliente: Dados do cliente
            loja_id: ID da loja (RLS)
            
        Returns:
            Dict com dados do cliente criado
        """
        try:
            # Adicionar loja_id aos dados
            dados_cliente['loja_id'] = loja_id
            
            # Inserir cliente
            result = (
                self.supabase
                .table('c_clientes')
                .insert(dados_cliente)
                .execute()
            )
            
            if not result.data:
                raise Exception("Erro ao inserir cliente")
            
            cliente_criado = result.data[0]
            logger.info(f"Cliente {cliente_criado['nome']} criado com ID {cliente_criado['id']}")
            
            return cliente_criado
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            raise Exception(f"Erro ao criar cliente: {str(e)}")
    
    async def listar_clientes(self, loja_id: str, filters: Optional[ClienteFilters] = None, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lista clientes com filtros aplicados
        
        Args:
            loja_id: ID da loja (RLS)
            filters: Filtros opcionais
            skip: Paginação - registros a pular
            limit: Paginação - limite de registros
            
        Returns:
            List[Dict]: Lista de clientes
        """
        try:
            # Query base
            query = (
                self.supabase
                .table('c_clientes')
                .select('*')
                .eq('loja_id', loja_id)
            )
            
            # Aplicar filtros se fornecidos
            if filters:
                if filters.nome:
                    query = query.ilike('nome', f'%{filters.nome}%')
                
                if filters.cpf_cnpj:
                    query = query.eq('cpf_cnpj', filters.cpf_cnpj)
                
                if filters.telefone:
                    query = query.ilike('telefone', f'%{filters.telefone}%')
                
                if filters.cidade:
                    query = query.ilike('cidade', f'%{filters.cidade}%')
                
                if filters.tipo_venda:
                    query = query.eq('tipo_venda', filters.tipo_venda.value)
                
                if filters.procedencia:
                    query = query.ilike('procedencia', f'%{filters.procedencia}%')
            
            # Executar query com paginação
            result = (
                query
                .order('created_at', desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )
            
            logger.debug(f"Listados {len(result.data)} clientes da loja {loja_id}")
            return result.data
            
        except Exception as e:
            logger.error(f"Erro ao listar clientes: {str(e)}")
            raise Exception(f"Erro ao listar clientes: {str(e)}")
    
    async def obter_cliente(self, cliente_id: str, loja_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém cliente por ID
        
        Args:
            cliente_id: ID do cliente
            loja_id: ID da loja (RLS)
            
        Returns:
            Dict com dados do cliente ou None se não encontrado
        """
        try:
            result = (
                self.supabase
                .table('c_clientes')
                .select('*')
                .eq('id', cliente_id)
                .eq('loja_id', loja_id)  # RLS
                .execute()
            )
            
            if result.data:
                logger.debug(f"Cliente {cliente_id} encontrado")
                return result.data[0]
            else:
                logger.warning(f"Cliente {cliente_id} não encontrado na loja {loja_id}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao obter cliente: {str(e)}")
    
    async def atualizar_cliente(self, cliente_id: str, dados_atualizacao: Dict[str, Any], loja_id: str) -> Dict[str, Any]:
        """
        Atualiza dados de um cliente
        
        Args:
            cliente_id: ID do cliente
            dados_atualizacao: Dados para atualizar
            loja_id: ID da loja (RLS)
            
        Returns:
            Dict com dados do cliente atualizado
        """
        try:
            # Adicionar timestamp de atualização
            from datetime import datetime
            dados_atualizacao['updated_at'] = datetime.utcnow().isoformat()
            
            # Atualizar cliente
            result = (
                self.supabase
                .table('c_clientes')
                .update(dados_atualizacao)
                .eq('id', cliente_id)
                .eq('loja_id', loja_id)  # RLS
                .execute()
            )
            
            if not result.data:
                raise Exception("Cliente não encontrado ou erro na atualização")
            
            cliente_atualizado = result.data[0]
            logger.info(f"Cliente {cliente_id} atualizado com sucesso")
            
            return cliente_atualizado
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")
    
    async def excluir_cliente(self, cliente_id: str, loja_id: str) -> bool:
        """
        Exclui cliente (soft delete)
        
        Args:
            cliente_id: ID do cliente
            loja_id: ID da loja (RLS)
            
        Returns:
            bool: True se excluído com sucesso
        """
        try:
            # Soft delete - marcar como excluído
            from datetime import datetime
            
            result = (
                self.supabase
                .table('c_clientes')
                .update({
                    'excluido': True,
                    'excluido_em': datetime.utcnow().isoformat()
                })
                .eq('id', cliente_id)
                .eq('loja_id', loja_id)  # RLS
                .execute()
            )
            
            if not result.data:
                raise Exception("Cliente não encontrado")
            
            logger.info(f"Cliente {cliente_id} excluído com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao excluir cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao excluir cliente: {str(e)}")
    
    async def verificar_cpf_cnpj_existente(self, cpf_cnpj: str, loja_id: str, cliente_id_excluir: Optional[str] = None) -> bool:
        """
        Verifica se CPF/CNPJ já existe na loja
        
        Args:
            cpf_cnpj: CPF ou CNPJ para verificar
            loja_id: ID da loja
            cliente_id_excluir: ID do cliente a excluir da verificação (para updates)
            
        Returns:
            bool: True se já existe
        """
        try:
            query = (
                self.supabase
                .table('c_clientes')
                .select('id')
                .eq('cpf_cnpj', cpf_cnpj)
                .eq('loja_id', loja_id)
                .is_('excluido', 'null')  # Não considerar excluídos
            )
            
            # Excluir cliente específico da verificação (para updates)
            if cliente_id_excluir:
                query = query.neq('id', cliente_id_excluir)
            
            result = query.execute()
            
            existe = len(result.data) > 0
            if existe:
                logger.warning(f"CPF/CNPJ {cpf_cnpj} já existe na loja {loja_id}")
            
            return existe
            
        except Exception as e:
            logger.error(f"Erro ao verificar CPF/CNPJ: {str(e)}")
            raise Exception(f"Erro ao verificar CPF/CNPJ: {str(e)}")


# Função auxiliar para compatibilidade com código existente
async def repo_list_clientes():
    """Função legacy - TODO: migrar para ClienteRepository.listar_clientes()"""
    # TODO: call Supabase HTTP API
    return []
