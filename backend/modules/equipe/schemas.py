
# Pydantic models for equipe
from pydantic import BaseModel

class EquipeBase(BaseModel):
    pass

class EquipeCreate(EquipeBase):
    pass

class EquipeResponse(EquipeBase):
    id: str
