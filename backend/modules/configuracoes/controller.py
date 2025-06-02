
# FastAPI routes for configuracoes
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/configuracoes', tags=['configuracoes'])

@router.get('/', response_model=list[dict])
async def list_configuracoes():
    return await repo_list_configuracoes()
