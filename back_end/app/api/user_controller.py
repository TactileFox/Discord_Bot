import services.user_service as user_service
from fastapi import APIRouter, HTTPException
from database.database import acquire_connection
from models.user import User

router = APIRouter(prefix='/users')


@router.get('/{id}', response_model=User)
async def get_user_by_id(
    id: int
) -> User:
    async with acquire_connection() as conn:
        user = await user_service.get_by_id(conn, id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return user
