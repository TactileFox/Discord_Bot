import services.user_service as user_service
from asyncpg import Connection
from fastapi import HTTPException
from typing import List
from models.user_mention import UserMention
from services.user_mention_mapping import map_user_mention_row


async def get_by_message_id(
        conn: Connection, message_id: int
) -> List[UserMention] | None:

    user_mention_data = await conn.fetch(
        'SELECT * FROM "UserMentions" WHERE "MessageId" = $1', message_id
    )
    if not user_mention_data:
        return None
    user_mentions = []
    for record in user_mention_data:
        recipient_id = record['RecipientId']
        recipient = await user_service.get_by_id(conn, recipient_id)
        if not recipient:
            raise HTTPException(
                status_code=404,
                detail=f'Recipient {recipient_id} not found'
            )
        user_mentions.append(map_user_mention_row(record, recipient))
    return user_mentions
