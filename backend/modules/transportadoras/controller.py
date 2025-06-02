
# FastAPI routes for transportadoras
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/transportadoras', tags=['transportadoras'])

@router.get('/', response_model=list[dict])
async def list_transportadoras():
    return await repo_list_transportadoras()
