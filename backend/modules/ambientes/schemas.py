
# Pydantic models for ambientes
from pydantic import BaseModel

class AmbientesBase(BaseModel):
    pass

class AmbientesCreate(AmbientesBase):
    pass

class AmbientesResponse(AmbientesBase):
    id: str
