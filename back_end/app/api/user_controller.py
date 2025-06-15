import app.services.user_service as user_service
from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException
from app.database.database import acquire_connection
from app.models.user import User

router = APIRouter(prefix='/users')


@router.get('/{id}', response_model=User)
async def get_user_by_id(
    id: int,
    conn: Connection = Depends(acquire_connection())
) -> User:
    user = user_service.get_by_id(conn, id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user
