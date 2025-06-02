
# Pydantic models for contratos
from pydantic import BaseModel

class ContratosBase(BaseModel):
    pass

class ContratosCreate(ContratosBase):
    pass

class ContratosResponse(ContratosBase):
    id: str
