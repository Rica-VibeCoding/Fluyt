
# FastAPI routes for ambientes
from fastapi import APIRouter, Depends
from .schemas import *
from .repository import *

router = APIRouter(prefix='/ambientes', tags=['ambientes'])

@router.get('/', response_model=list[dict])
async def list_ambientes():
    return await repo_list_ambientes()
