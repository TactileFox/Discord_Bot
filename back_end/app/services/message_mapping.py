from asyncpg import Record
from typing import List
from models.attachment import Attachment
from models.message import Message
from models.user import User
from models.guild import Guild
from models.channel import Channel
from models.user_mention import UserMention


def map_message_row(
    record: Record, author: User,
    guild: Guild, channel: Channel,
    attachments: List[Attachment] = None,
    user_mentions: List[UserMention] = None
) -> Message:
    message = Message(
        attachments=attachments,
        author=author,
        channel=channel,
        content=record['Content'],
        create_date=record['CreateDateUTC'],
        delete_date=record.get('DeleteDateUTC', None),
        deleted=record['Deleted'],
        edited=record['Edited'],
        guild=guild,
        id=record['Id'],
        update_date=record.get('UpdateDateUTC', None),
        user_mentions=user_mentions
    )
    return message
