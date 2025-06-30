import services.channel_service as channel_service
from fastapi import APIRouter, HTTPException
from database.database import acquire_connection
from models.channel import Channel

router = APIRouter(prefix='/channels')


@router.get('/{id}', response_model=Channel)
async def get_channel_by_id(
    id: int
) -> Channel:
    async with acquire_connection() as conn:
        channel = await channel_service.get_by_id(conn, id)
        if not channel:
            raise HTTPException(status_code=404, detail='Channel not found')
        return channel
