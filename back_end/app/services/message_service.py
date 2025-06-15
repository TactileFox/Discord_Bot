import services.channel_service as channel_service
import services.user_service as user_service
from asyncpg import Connection
from models.message import Message
from services.message_mapping import map_message_row


async def get_by_id(conn: Connection, id: int) -> Message | None:
    message_data = conn.fetchrow('SELECT * FROM ')
    if message_data:
        author = user_service.get_by_id(conn, message_data['UserId'])
        channel = channel_service.get_by_id(conn, message_data['ChannelId'])
        return map_message_row(message_data, author, channel.guild, channel)
    return None
