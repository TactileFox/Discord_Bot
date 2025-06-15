import app.services.guild_service as guild_service
from asyncpg import Connection
from app.models.channel import Channel
from app.services.channel_mapping import map_channel_row


def get_by_id(conn: Connection, id: int) -> Channel | None:
    channel_data = conn.fetchrow('SELECT * FROM "Channel" WHERE "Id" = $1', id)
    if channel_data:
        guild = guild_service.get_by_id(conn, channel_data['GuildId'])
        return map_channel_row(channel_data, guild)
    return None
