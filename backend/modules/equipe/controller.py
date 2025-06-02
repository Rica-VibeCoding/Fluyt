
# FastAPI routes for equipe
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/equipe', tags=['equipe'])

@router.get('/', response_model=list[dict])
async def list_equipe():
    return await repo_list_equipe()
