
# FastAPI routes for auditoria
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/auditoria', tags=['auditoria'])

@router.get('/', response_model=list[dict])
async def list_auditoria():
    return await repo_list_auditoria()
