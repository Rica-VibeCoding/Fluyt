
# FastAPI routes for montadores
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/montadores', tags=['montadores'])

@router.get('/', response_model=list[dict])
async def list_montadores():
    return await repo_list_montadores()
