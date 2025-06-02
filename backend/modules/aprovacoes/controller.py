
# FastAPI routes for aprovacoes
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/aprovacoes', tags=['aprovacoes'])

@router.get('/', response_model=list[dict])
async def list_aprovacoes():
    return await repo_list_aprovacoes()
