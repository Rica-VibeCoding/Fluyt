# Data access layer for clientes

from typing import List, Dict, Any, Optional
import logging
from supabase import Client
from datetime import datetime

# Configurar logger
logger = logging.getLogger(__name__)


class ClienteRepository:
    """
    Repository para operações de clientes com Supabase - APENAS DADOS
    Stack: FastAPI + Python + Supabase (conforme PRD.md)
    
    Responsabilidade: Acesso a dados, queries diretas ao Supabase
    Lógica de negócio: ClienteService
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # ===== MÉTODOS CRUD PARA SERVICE =====
    
    async def criar_cliente(self, dados_cliente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria novo cliente no banco de dados
        
        Args:
            dados_cliente: Dados do cliente para inserir
            
        Returns:
            Dict[str, Any]: Cliente criado com ID gerado
        """
        try:
            # Adicionar timestamps
            dados_insercao = {
                **dados_cliente,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = (
                self.supabase
                .table('c_clientes')
                .insert(dados_insercao)
                .execute()
            )
            
            if not result.data:
                raise Exception("Erro ao inserir cliente")
            
            cliente_criado = result.data[0]
            
            logger.info(f"Cliente criado com ID {cliente_criado['id']}")
            
            return cliente_criado
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            raise Exception(f"Erro ao criar cliente: {str(e)}")
    
    async def listar_clientes(self, loja_id: str, skip: int = 0, limit: int = 50, filtro_nome: Optional[str] = None, filtro_tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista clientes da loja com filtros opcionais
        
        Args:
            loja_id: ID da loja
            skip: Registros para pular
            limit: Limite de registros
            filtro_nome: Filtro por nome (opcional)
            filtro_tipo: Filtro por tipo de venda (opcional)
            
        Returns:
            List[Dict[str, Any]]: Lista de clientes
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
            if filtro_nome:
                query = query.ilike('nome', f'%{filtro_nome}%')
            
            if filtro_tipo:
                query = query.eq('tipo_venda', filtro_tipo)
            
            # Aplicar paginação e ordenação
            query = query.order('created_at', desc=True).range(skip, skip + limit - 1)
            
            result = query.execute()
            
            logger.debug(f"Listados {len(result.data)} clientes para loja {loja_id}")
            
            return result.data
            
        except Exception as e:
            logger.error(f"Erro ao listar clientes: {str(e)}")
            raise Exception(f"Erro ao listar clientes: {str(e)}")
    
    async def obter_cliente_por_id(self, cliente_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém cliente por ID
        
        Args:
            cliente_id: ID do cliente
            
        Returns:
            Optional[Dict[str, Any]]: Dados do cliente ou None se não encontrado
        """
        try:
            result = (
                self.supabase
                .table('c_clientes')
                .select('*')
                .eq('id', cliente_id)
                .single()
                .execute()
            )
            
            if result.data:
                logger.debug(f"Cliente {cliente_id} encontrado")
                return result.data
            else:
                logger.warning(f"Cliente {cliente_id} não encontrado")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao obter cliente: {str(e)}")
    
    async def atualizar_cliente(self, cliente_id: str, dados_atualizacao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza cliente existente
        
        Args:
            cliente_id: ID do cliente
            dados_atualizacao: Dados para atualizar
            
        Returns:
            Dict[str, Any]: Cliente atualizado
        """
        try:
            # Adicionar timestamp de atualização
            dados_atualizacao['updated_at'] = datetime.now().isoformat()
            
            result = (
                self.supabase
                .table('c_clientes')
                .update(dados_atualizacao)
                .eq('id', cliente_id)
                .execute()
            )
            
            if not result.data:
                raise Exception("Cliente não encontrado para atualização")
            
            logger.info(f"Cliente {cliente_id} atualizado com sucesso")
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")
    
    async def excluir_cliente(self, cliente_id: str):
        """
        Exclui cliente (soft delete - marca como inativo)
        
        Args:
            cliente_id: ID do cliente
        """
        try:
            # Soft delete - marcar como excluído
            result = (
                self.supabase
                .table('c_clientes')
                .update({
                    'ativo': False,
                    'deleted_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                .eq('id', cliente_id)
                .execute()
            )
            
            if not result.data:
                raise Exception("Cliente não encontrado para exclusão")
            
            logger.info(f"Cliente {cliente_id} excluído com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao excluir cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao excluir cliente: {str(e)}")
    
    async def buscar_por_cpf_cnpj(self, cpf_cnpj: str, loja_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente por CPF/CNPJ na loja
        
        Args:
            cpf_cnpj: CPF ou CNPJ do cliente
            loja_id: ID da loja
            
        Returns:
            Optional[Dict[str, Any]]: Cliente encontrado ou None
        """
        try:
            result = (
                self.supabase
                .table('c_clientes')
                .select('*')
                .eq('cpf_cnpj', cpf_cnpj)
                .eq('loja_id', loja_id)
                .single()
                .execute()
            )
            
            return result.data if result.data else None
            
        except Exception as e:
            # Se não encontrar, retorna None (não é erro)
            if "No rows found" in str(e) or "Multiple rows found" in str(e):
                return None
            
            logger.error(f"Erro ao buscar cliente por CPF/CNPJ {cpf_cnpj}: {str(e)}")
            raise Exception(f"Erro ao buscar cliente: {str(e)}")
    
    async def buscar_clientes(self, termo: str, loja_id: str) -> List[Dict[str, Any]]:
        """
        Busca clientes por termo (nome, CPF, telefone)
        
        Args:
            termo: Termo de busca
            loja_id: ID da loja
            
        Returns:
            List[Dict[str, Any]]: Clientes encontrados
        """
        try:
            # Busca em múltiplos campos
            result = (
                self.supabase
                .table('c_clientes')
                .select('*')
                .eq('loja_id', loja_id)
                .or_(f'nome.ilike.%{termo}%,cpf_cnpj.ilike.%{termo}%,telefone.ilike.%{termo}%')
                .order('nome')
                .limit(20)  # Limitar resultados de busca
                .execute()
            )
            
            logger.debug(f"Busca por '{termo}' retornou {len(result.data)} clientes")
            
            return result.data
            
        except Exception as e:
            logger.error(f"Erro ao buscar clientes com termo '{termo}': {str(e)}")
            raise Exception(f"Erro ao buscar clientes: {str(e)}")
    
    async def verificar_cliente_tem_orcamentos(self, cliente_id: str) -> bool:
        """
        Verifica se cliente possui orçamentos
        
        Args:
            cliente_id: ID do cliente
            
        Returns:
            bool: True se cliente tem orçamentos
        """
        try:
            result = (
                self.supabase
                .table('c_orcamentos')
                .select('id')
                .eq('cliente_id', cliente_id)
                .limit(1)
                .execute()
            )
            
            tem_orcamentos = len(result.data) > 0
            
            logger.debug(f"Cliente {cliente_id} {'tem' if tem_orcamentos else 'não tem'} orçamentos")
            
            return tem_orcamentos
            
        except Exception as e:
            logger.error(f"Erro ao verificar orçamentos do cliente {cliente_id}: {str(e)}")
            # Em caso de erro, assumir que tem orçamentos (mais seguro)
            return True


# Função auxiliar para compatibilidade com código existente
async def repo_list_clientes():
    """Função legacy - TODO: migrar para ClienteRepository.listar_clientes()"""
    # TODO: call Supabase HTTP API
    return []
