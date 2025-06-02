
# FastAPI routes for contratos
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/contratos', tags=['contratos'])

@router.get('/', response_model=list[dict])
async def list_contratos():
    return await repo_list_contratos()
