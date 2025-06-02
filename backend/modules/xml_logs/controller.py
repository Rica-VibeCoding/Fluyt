
# FastAPI routes for xml_logs
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/xml_logs', tags=['xml_logs'])

@router.get('/', response_model=list[dict])
async def list_xml_logs():
    return await repo_list_xml_logs()
