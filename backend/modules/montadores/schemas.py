
# Pydantic models for montadores
from pydantic import BaseModel

class MontadoresBase(BaseModel):
    pass

class MontadoresCreate(MontadoresBase):
    pass

class MontadoresResponse(MontadoresBase):
    id: str
