from asyncpg import Record
from models.message import Message
from models.user import User
from models.guild import Guild
from models.channel import Channel


def map_message_row(
    record: Record, author: User, guild: Guild, channel: Channel
) -> Message:
    message = Message(
        author=author,
        channel=channel,
        content=record['Content'],
        create_date=record['CreateDateUTC'],
        delete_date=record.get('DeleteDateUTC', None),
        deleted=record['Deleted'],
        edited=record['Edited'],
        guild=guild,
        id=record['Id'],
        update_date=record.get('UpdateDateUTC', None)
    )
    return message
