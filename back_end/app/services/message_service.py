from fastapi import HTTPException
import services.channel_service as channel_service
import services.user_service as user_service
import services.user_mention_service as user_mention_service
from asyncpg import Connection
from models.channel import Channel
from models.message import Message
from models.user import User
from services.message_mapping import map_message_row


async def get_user_by_id(conn: Connection, id: int) -> User:
    author = await user_service.get_by_id(conn, id)
    if not author:
        raise HTTPException(status_code=404, detail=f"User {id} not found")
    return author


async def get_channel_by_id(conn: Connection, id: int) -> Channel:
    channel = await channel_service.get_by_id(conn, id)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {id} not found")
    return channel


async def get_by_id(conn: Connection, id: int) -> Message | None:
    message_data = await conn.fetchrow(
        'SELECT * FROM "Message" WHERE "Id" = $1', id
    )

    if message_data:
        author = await get_user_by_id(conn, message_data['UserId'])
        channel = await get_channel_by_id(conn, message_data['ChannelId'])
        user_mentions = await user_mention_service.get_by_message_id(
            conn, message_data['Id']
        )
        return map_message_row(
            message_data, author, channel.guild,
            channel, None, user_mentions
        )
    return None
