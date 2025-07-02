from asyncpg import Connection
from typing import List
from models.attachment import Attachment
from services.attachment_mapping import map_attachment_row


async def get_by_message_id(
        conn: Connection, message_id: int
) -> List[Attachment] | None:
    attachment_data = await conn.fetch(
        'SELECT * FROM "Attachments" WHERE "MessageId" = $1', message_id
    )
    if not attachment_data:
        return None
    attachments = []
    for record in attachment_data:
        attachments.append(map_attachment_row(record))
    return attachments
