
# Pydantic models for transportadoras
from pydantic import BaseModel

class TransportadorasBase(BaseModel):
    pass

class TransportadorasCreate(TransportadorasBase):
    pass

class TransportadorasResponse(TransportadorasBase):
    id: str
