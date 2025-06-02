# Business logic helpers for clientes

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid

from .repository import ClienteRepository
from .schemas import ClienteCreate, ClienteUpdate, ClienteResponse

# Configurar logger
logger = logging.getLogger(__name__)


class ClienteService:
    """
    Service layer para clientes - CRUD básico e validações
    Stack: FastAPI + Python + Supabase (conforme PRD.md)
    
    Responsabilidade: Lógica de negócio, validações de cliente
    """
    
    def __init__(self, repository: ClienteRepository):
        self.repository = repository

    # ===== MÉTODOS CRUD PARA CONTROLLERS =====
    
    async def criar_cliente(self, cliente_data: ClienteCreate, current_user: Dict[str, Any]) -> ClienteResponse:
        """
        Cria novo cliente
        
        Args:
            cliente_data: Dados do cliente
            current_user: Usuário autenticado
            
        Returns:
            ClienteResponse: Cliente criado
        """
        try:
            loja_id = current_user['loja_id']
            
            logger.info(f"Criando cliente {cliente_data.nome} para loja {loja_id}")
            
            # Validar se CPF/CNPJ já existe na loja (regra de negócio)
            if cliente_data.cpf_cnpj:
                cliente_existente = await self.repository.buscar_por_cpf_cnpj(
                    cliente_data.cpf_cnpj, loja_id
                )
                if cliente_existente:
                    raise Exception(f"Cliente com CPF/CNPJ {cliente_data.cpf_cnpj} já existe nesta loja")
            
            # Preparar dados para inserção
            dados_insercao = {
                'nome': cliente_data.nome,
                'cpf_cnpj': cliente_data.cpf_cnpj,
                'telefone': cliente_data.telefone,
                'email': cliente_data.email,
                'endereco': cliente_data.endereco,
                'cidade': cliente_data.cidade,
                'cep': cliente_data.cep,
                'loja_id': loja_id,
                'tipo_venda': cliente_data.tipo_venda.value if cliente_data.tipo_venda else 'NORMAL',
                'observacao': cliente_data.observacao
            }
            
            # Criar cliente
            cliente_criado = await self.repository.criar_cliente(dados_insercao)
            
            logger.info(f"Cliente {cliente_criado['id']} criado com sucesso")
            
            return ClienteResponse(**cliente_criado)
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            raise Exception(f"Erro ao criar cliente: {str(e)}")
    
    async def listar_clientes(self, current_user: Dict[str, Any], skip: int = 0, limit: int = 50, filtro_nome: Optional[str] = None, filtro_tipo: Optional[str] = None) -> List[ClienteResponse]:
        """
        Lista clientes da loja com filtros opcionais
        
        Args:
            current_user: Usuário autenticado
            skip: Registros para pular
            limit: Limite de registros
            filtro_nome: Filtro por nome (opcional)
            filtro_tipo: Filtro por tipo de venda (opcional)
            
        Returns:
            List[ClienteResponse]: Lista de clientes
        """
        try:
            loja_id = current_user['loja_id']
            
            logger.debug(f"Listando clientes para loja {loja_id}")
            
            clientes = await self.repository.listar_clientes(loja_id, skip, limit, filtro_nome, filtro_tipo)
            
            return [ClienteResponse(**cliente) for cliente in clientes]
            
        except Exception as e:
            logger.error(f"Erro ao listar clientes: {str(e)}")
            raise Exception(f"Erro ao listar clientes: {str(e)}")
    
    async def obter_cliente(self, cliente_id: uuid.UUID, current_user: Dict[str, Any]) -> ClienteResponse:
        """
        Obtém cliente por ID
        
        Args:
            cliente_id: ID do cliente
            current_user: Usuário autenticado
            
        Returns:
            ClienteResponse: Dados do cliente
        """
        try:
            cliente = await self.repository.obter_cliente_por_id(str(cliente_id))
            
            if not cliente:
                raise Exception("Cliente não encontrado")
            
            # Verificar se cliente pertence à loja do usuário
            if cliente['loja_id'] != current_user['loja_id'] and current_user['perfil'] != 'ADMIN_MASTER':
                raise Exception("Sem permissão para acessar este cliente")
            
            return ClienteResponse(**cliente)
            
        except Exception as e:
            logger.error(f"Erro ao obter cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao obter cliente: {str(e)}")
    
    async def atualizar_cliente(self, cliente_id: uuid.UUID, cliente_data: ClienteUpdate, current_user: Dict[str, Any]) -> ClienteResponse:
        """
        Atualiza cliente existente
        
        Args:
            cliente_id: ID do cliente
            cliente_data: Dados para atualização
            current_user: Usuário autenticado
            
        Returns:
            ClienteResponse: Cliente atualizado
        """
        try:
            # Verificar se cliente existe e permissões
            cliente_atual = await self.repository.obter_cliente_por_id(str(cliente_id))
            
            if not cliente_atual:
                raise Exception("Cliente não encontrado")
            
            if cliente_atual['loja_id'] != current_user['loja_id'] and current_user['perfil'] != 'ADMIN_MASTER':
                raise Exception("Sem permissão para editar este cliente")
            
            # Verificar CPF/CNPJ duplicado se mudou
            if cliente_data.cpf_cnpj and cliente_data.cpf_cnpj != cliente_atual['cpf_cnpj']:
                cliente_existente = await self.repository.buscar_por_cpf_cnpj(
                    cliente_data.cpf_cnpj, cliente_atual['loja_id']
                )
                if cliente_existente and cliente_existente['id'] != str(cliente_id):
                    raise Exception(f"CPF/CNPJ {cliente_data.cpf_cnpj} já existe para outro cliente")
            
            # Preparar dados de atualização apenas com campos não-nulos
            dados_atualizacao = {}
            
            if cliente_data.nome is not None:
                dados_atualizacao['nome'] = cliente_data.nome
            if cliente_data.cpf_cnpj is not None:
                dados_atualizacao['cpf_cnpj'] = cliente_data.cpf_cnpj
            if cliente_data.telefone is not None:
                dados_atualizacao['telefone'] = cliente_data.telefone
            if cliente_data.email is not None:
                dados_atualizacao['email'] = cliente_data.email
            if cliente_data.endereco is not None:
                dados_atualizacao['endereco'] = cliente_data.endereco
            if cliente_data.cidade is not None:
                dados_atualizacao['cidade'] = cliente_data.cidade
            if cliente_data.cep is not None:
                dados_atualizacao['cep'] = cliente_data.cep
            if cliente_data.tipo_venda is not None:
                dados_atualizacao['tipo_venda'] = cliente_data.tipo_venda.value
            if cliente_data.observacao is not None:
                dados_atualizacao['observacao'] = cliente_data.observacao
            
            # Atualizar no banco
            cliente_atualizado = await self.repository.atualizar_cliente(str(cliente_id), dados_atualizacao)
            
            logger.info(f"Cliente {cliente_id} atualizado com sucesso")
            
            return ClienteResponse(**cliente_atualizado)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")
    
    async def excluir_cliente(self, cliente_id: uuid.UUID, current_user: Dict[str, Any]):
        """
        Exclui cliente (soft delete)
        
        Args:
            cliente_id: ID do cliente
            current_user: Usuário autenticado
        """
        try:
            cliente = await self.repository.obter_cliente_por_id(str(cliente_id))
            
            if not cliente:
                raise Exception("Cliente não encontrado")
            
            if cliente['loja_id'] != current_user['loja_id'] and current_user['perfil'] != 'ADMIN_MASTER':
                raise Exception("Sem permissão para excluir este cliente")
            
            # Verificar se cliente tem orçamentos (regra de negócio)
            tem_orcamentos = await self.repository.verificar_cliente_tem_orcamentos(str(cliente_id))
            if tem_orcamentos:
                raise Exception("Cliente não pode ser excluído pois possui orçamentos")
            
            await self.repository.excluir_cliente(str(cliente_id))
            
            logger.info(f"Cliente {cliente_id} excluído com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao excluir cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao excluir cliente: {str(e)}")
    
    async def buscar_clientes(self, termo: str, current_user: Dict[str, Any]) -> List[ClienteResponse]:
        """
        Busca clientes por termo (nome, CPF, telefone)
        
        Args:
            termo: Termo de busca
            current_user: Usuário autenticado
            
        Returns:
            List[ClienteResponse]: Clientes encontrados
        """
        try:
            loja_id = current_user['loja_id']
            
            clientes = await self.repository.buscar_clientes(termo, loja_id)
            
            return [ClienteResponse(**cliente) for cliente in clientes]
            
        except Exception as e:
            logger.error(f"Erro ao buscar clientes com termo '{termo}': {str(e)}")
            raise Exception(f"Erro ao buscar clientes: {str(e)}")
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _validar_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """
        Valida formato de CPF ou CNPJ
        
        Args:
            cpf_cnpj: CPF ou CNPJ para validar
            
        Returns:
            bool: True se válido
        """
        # TODO: Implementar validação de CPF/CNPJ
        # Por enquanto apenas verificar se não está vazio
        return bool(cpf_cnpj and cpf_cnpj.strip())
    
    def _normalizar_cpf_cnpj(self, cpf_cnpj: str) -> str:
        """
        Remove caracteres especiais do CPF/CNPJ
        
        Args:
            cpf_cnpj: CPF ou CNPJ com formatação
            
        Returns:
            str: CPF/CNPJ apenas com números
        """
        if not cpf_cnpj:
            return ""
        
        return ''.join(char for char in cpf_cnpj if char.isdigit())
