
# Pydantic models for configuracoes
from pydantic import BaseModel

class ConfiguracoesBase(BaseModel):
    pass

class ConfiguracoesCreate(ConfiguracoesBase):
    pass

class ConfiguracoesResponse(ConfiguracoesBase):
    id: str
