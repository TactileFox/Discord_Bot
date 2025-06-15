from asyncpg import Connection
from models.guild import Guild
from services.guild_mapping import map_guild_row


async def get_by_id(conn: Connection, id: int) -> Guild | None:
    guild_data = conn.fetchrow('SELECT * FROM "Guild" WHERE "Id" = $1', id)
    if guild_data:
        return map_guild_row(guild_data)
    return None
