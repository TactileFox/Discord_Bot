import app.services.guild_service as guild_service
from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException
from app.database.database import acquire_connection
from app.models.guild import Guild


router = APIRouter(prefix='/guild')  # may need tags?


@router.get('/{id}', response_model=Guild)
def get_guild_by_id(
    id: int,
    conn: Connection = Depends(acquire_connection())
) -> Guild:
    guild = guild_service.get_by_id(conn, id)
    if not guild:
        raise HTTPException(status_code=404, detail='Guild not found')
    else:
        return guild
