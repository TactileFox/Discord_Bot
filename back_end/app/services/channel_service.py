import services.guild_service as guild_service
from asyncpg import Connection
from fastapi import HTTPException
from models.channel import Channel
from services.channel_mapping import map_channel_row


async def get_by_id(conn: Connection, id: int) -> Channel | None:
    channel_data = await conn.fetchrow(
        'SELECT * FROM "Channel" WHERE "Id" = $1', id
        )
    if channel_data:
        guild = await guild_service.get_by_id(conn, channel_data['GuildId'])
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        return map_channel_row(channel_data, guild)
    raise HTTPException(status_code=404, detail='Channel not found')
