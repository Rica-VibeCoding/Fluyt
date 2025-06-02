
# Pydantic models for aprovacoes
from pydantic import BaseModel

class AprovacoesBase(BaseModel):
    pass

class AprovacoesCreate(AprovacoesBase):
    pass

class AprovacoesResponse(AprovacoesBase):
    id: str
