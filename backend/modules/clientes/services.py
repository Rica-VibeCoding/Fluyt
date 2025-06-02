"""
Service layer para clientes - lógica de negócio e validações.
Responsabilidade: Orquestração, validações, regras de negócio.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .repository import ClienteRepository
from .schemas import ClienteCreate, ClienteUpdate, ClienteResponse, ClienteListItem, ClienteFilters

# Configurar logger
logger = logging.getLogger(__name__)


class ClienteService:
    """
    Service layer para clientes - lógica de negócio
    
    Responsabilidade: Validações, regras de negócio, orquestração
    """
    
    def __init__(self, supabase_client):
        self.repository = ClienteRepository(supabase_client)
    
    async def criar_cliente(self, cliente_data: ClienteCreate, current_user: Dict[str, Any]) -> ClienteResponse:
        """
        Cria um novo cliente com validações de negócio
        
        Args:
            cliente_data: Dados do cliente
            current_user: Usuário logado (contém loja_id)
            
        Returns:
            ClienteResponse: Cliente criado
        """
        try:
            loja_id = current_user['loja_id']
            
            logger.info(f"Criando cliente {cliente_data.nome} na loja {loja_id}")
            
            # Validar se CPF/CNPJ já existe na loja
            cpf_cnpj_existe = await self.repository.verificar_cpf_cnpj_existente(
                cliente_data.cpf_cnpj, 
                loja_id
            )
            
            if cpf_cnpj_existe:
                raise Exception(f"CPF/CNPJ {cliente_data.cpf_cnpj} já está cadastrado nesta loja")
            
            # Preparar dados para inserção
            dados_cliente = {
                'nome': cliente_data.nome,
                'cpf_cnpj': cliente_data.cpf_cnpj,
                'telefone': cliente_data.telefone,
                'email': cliente_data.email,
                'endereco': cliente_data.endereco,
                'cidade': cliente_data.cidade,
                'cep': cliente_data.cep,
                'tipo_venda': cliente_data.tipo_venda.value,
                'procedencia': cliente_data.procedencia,
                'observacao': cliente_data.observacao
            }
            
            # Criar cliente
            cliente_criado = await self.repository.criar_cliente(dados_cliente, loja_id)
            
            logger.info(f"Cliente {cliente_data.nome} criado com sucesso: ID {cliente_criado['id']}")
            
            # Retornar como ClienteResponse
            return ClienteResponse(**cliente_criado)
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {str(e)}")
            raise Exception(f"Erro ao criar cliente: {str(e)}")
    
    async def listar_clientes(self, filters: Optional[ClienteFilters], current_user: Dict[str, Any], skip: int = 0, limit: int = 50) -> List[ClienteListItem]:
        """
        Lista clientes com filtros aplicados
        
        Args:
            filters: Filtros opcionais
            current_user: Usuário logado
            skip: Paginação - registros a pular
            limit: Paginação - limite de registros
            
        Returns:
            List[ClienteListItem]: Lista de clientes
        """
        try:
            loja_id = current_user['loja_id']
            
            # Buscar clientes
            clientes_data = await self.repository.listar_clientes(loja_id, filters, skip, limit)
            
            # Converter para ClienteListItem
            clientes = []
            for cliente_data in clientes_data:
                cliente_item = ClienteListItem(
                    id=cliente_data['id'],
                    nome=cliente_data['nome'],
                    telefone=cliente_data['telefone'],
                    email=cliente_data.get('email'),
                    cidade=cliente_data['cidade'],
                    tipo_venda=cliente_data['tipo_venda'],
                    procedencia=cliente_data.get('procedencia'),
                    created_at=cliente_data['created_at']
                )
                clientes.append(cliente_item)
            
            logger.debug(f"Listados {len(clientes)} clientes da loja {loja_id}")
            return clientes
            
        except Exception as e:
            logger.error(f"Erro ao listar clientes: {str(e)}")
            raise Exception(f"Erro ao listar clientes: {str(e)}")
    
    async def obter_cliente(self, cliente_id: str, current_user: Dict[str, Any]) -> ClienteResponse:
        """
        Obtém cliente por ID
        
        Args:
            cliente_id: ID do cliente
            current_user: Usuário logado
            
        Returns:
            ClienteResponse: Cliente encontrado
        """
        try:
            loja_id = current_user['loja_id']
            
            # Buscar cliente
            cliente_data = await self.repository.obter_cliente(cliente_id, loja_id)
            
            if not cliente_data:
                raise Exception("Cliente não encontrado")
            
            # Retornar como ClienteResponse
            return ClienteResponse(**cliente_data)
            
        except Exception as e:
            logger.error(f"Erro ao obter cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao obter cliente: {str(e)}")
    
    async def atualizar_cliente(self, cliente_id: str, cliente_data: ClienteUpdate, current_user: Dict[str, Any]) -> ClienteResponse:
        """
        Atualiza cliente existente
        
        Args:
            cliente_id: ID do cliente
            cliente_data: Dados de atualização
            current_user: Usuário logado
            
        Returns:
            ClienteResponse: Cliente atualizado
        """
        try:
            loja_id = current_user['loja_id']
            
            # Verificar se cliente existe
            cliente_atual = await self.repository.obter_cliente(cliente_id, loja_id)
            if not cliente_atual:
                raise Exception("Cliente não encontrado")
            
            # Preparar dados de atualização (apenas campos fornecidos)
            dados_atualizacao = {}
            
            if cliente_data.nome is not None:
                dados_atualizacao['nome'] = cliente_data.nome
            
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
            
            if cliente_data.procedencia is not None:
                dados_atualizacao['procedencia'] = cliente_data.procedencia
            
            if cliente_data.observacao is not None:
                dados_atualizacao['observacao'] = cliente_data.observacao
            
            # Atualizar apenas se há dados para atualizar
            if dados_atualizacao:
                cliente_atualizado = await self.repository.atualizar_cliente(
                    cliente_id, 
                    dados_atualizacao, 
                    loja_id
                )
                
                logger.info(f"Cliente {cliente_id} atualizado com sucesso")
                return ClienteResponse(**cliente_atualizado)
            else:
                # Sem alterações, retornar cliente atual
                return ClienteResponse(**cliente_atual)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")
    
    async def excluir_cliente(self, cliente_id: str, current_user: Dict[str, Any]) -> bool:
        """
        Exclui cliente com validações de negócio
        
        Args:
            cliente_id: ID do cliente
            current_user: Usuário logado
            
        Returns:
            bool: True se excluído com sucesso
        """
        try:
            loja_id = current_user['loja_id']
            
            # Verificar se cliente existe
            cliente_atual = await self.repository.obter_cliente(cliente_id, loja_id)
            if not cliente_atual:
                raise Exception("Cliente não encontrado")
            
            # TODO: Verificar se cliente tem orçamentos/contratos associados
            # Se sim, apenas marcar como inativo ou bloquear exclusão
            
            # Excluir cliente
            sucesso = await self.repository.excluir_cliente(cliente_id, loja_id)
            
            if sucesso:
                logger.info(f"Cliente {cliente_id} ({cliente_atual['nome']}) excluído com sucesso")
            
            return sucesso
            
        except Exception as e:
            logger.error(f"Erro ao excluir cliente {cliente_id}: {str(e)}")
            raise Exception(f"Erro ao excluir cliente: {str(e)}")
    
    async def buscar_cliente_por_cpf_cnpj(self, cpf_cnpj: str, current_user: Dict[str, Any]) -> Optional[ClienteResponse]:
        """
        Busca cliente por CPF/CNPJ
        
        Args:
            cpf_cnpj: CPF ou CNPJ para buscar
            current_user: Usuário logado
            
        Returns:
            ClienteResponse ou None se não encontrado
        """
        try:
            loja_id = current_user['loja_id']
            
            # Limpar CPF/CNPJ (remover caracteres especiais)
            cpf_cnpj_limpo = ''.join(filter(str.isdigit, cpf_cnpj))
            
            # Buscar usando filtros
            filters = ClienteFilters(cpf_cnpj=cpf_cnpj_limpo)
            clientes = await self.repository.listar_clientes(loja_id, filters, 0, 1)
            
            if clientes:
                return ClienteResponse(**clientes[0])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar cliente por CPF/CNPJ: {str(e)}")
            raise Exception(f"Erro ao buscar cliente por CPF/CNPJ: {str(e)}")
    
    async def validar_dados_cliente(self, cliente_data: ClienteCreate) -> Dict[str, Any]:
        """
        Valida dados do cliente (regras de negócio específicas)
        
        Args:
            cliente_data: Dados do cliente para validar
            
        Returns:
            Dict com resultado da validação
        """
        try:
            erros = []
            warnings = []
            
            # Validação de CPF básica (algoritmo simplificado)
            if len(cliente_data.cpf_cnpj) == 11:
                # É CPF
                if cliente_data.cpf_cnpj == cliente_data.cpf_cnpj[0] * 11:
                    erros.append("CPF inválido: todos os dígitos são iguais")
            
            # Validação de telefone básica
            if len(cliente_data.telefone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
                erros.append("Telefone deve ter pelo menos 10 dígitos")
            
            # Validação de email mais rigorosa
            if cliente_data.email and '.' not in cliente_data.email:
                warnings.append("Email pode estar incompleto (sem domínio)")
            
            # Validação de CEP básica
            cep_numeros = ''.join(filter(str.isdigit, cliente_data.cep))
            if len(cep_numeros) != 8:
                erros.append("CEP deve ter 8 dígitos")
            
            resultado = {
                'valido': len(erros) == 0,
                'erros': erros,
                'warnings': warnings
            }
            
            logger.debug(f"Validação cliente: {resultado}")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na validação: {str(e)}")
            return {
                'valido': False,
                'erros': [f"Erro na validação: {str(e)}"],
                'warnings': []
            }
