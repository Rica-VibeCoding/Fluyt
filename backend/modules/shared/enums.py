
from enum import Enum
class PerfilUsuario(str, Enum):
    VENDEDOR = 'vendedor'
    GERENTE = 'gerente'
    MEDIDOR = 'medidor'
    ADMIN = 'admin'
