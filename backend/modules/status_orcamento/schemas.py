
# Pydantic models for status_orcamento
from pydantic import BaseModel

class Status_orcamentoBase(BaseModel):
    pass

class Status_orcamentoCreate(Status_orcamentoBase):
    pass

class Status_orcamentoResponse(Status_orcamentoBase):
    id: str
