import services.guild_service as guild_service
from fastapi import APIRouter, HTTPException
from database.database import acquire_connection
from models.guild import Guild


router = APIRouter(prefix='/guilds')  # may need tags?


@router.get('/{id}', response_model=Guild)
async def get_guild_by_id(
    id: int
) -> Guild:
    async with acquire_connection() as conn:
        guild = await guild_service.get_by_id(conn, id)
        if not guild:
            raise HTTPException(status_code=404, detail='Guild not found')
        else:
            return guild
