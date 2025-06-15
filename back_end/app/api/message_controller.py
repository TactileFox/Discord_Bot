import services.message_service as message_service
from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException
from database.database import acquire_connection
from models.message import Message

router = APIRouter(prefix='/messages')


@router.get('/{id}', response_model=Message)
async def get_message_by_id(
    id: int,
    conn: Connection = Depends(acquire_connection())
) -> Message:
    message = message_service.get_by_id(conn, id)
    if not message:
        raise HTTPException(status_code=404, detail='Message not found')
    return message
