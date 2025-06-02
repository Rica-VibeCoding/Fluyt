
# Pydantic models for auditoria
from pydantic import BaseModel

class AuditoriaBase(BaseModel):
    pass

class AuditoriaCreate(AuditoriaBase):
    pass

class AuditoriaResponse(AuditoriaBase):
    id: str
