
# Pydantic models for xml_logs
from pydantic import BaseModel

class Xml_logsBase(BaseModel):
    pass

class Xml_logsCreate(Xml_logsBase):
    pass

class Xml_logsResponse(Xml_logsBase):
    id: str
