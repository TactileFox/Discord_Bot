from asyncpg import Record
from models.channel import Channel
from models.enums import ChannelType
from models.guild import Guild


def map_channel_row(record: Record, guild: Guild) -> Channel:
    channel = Channel(
        category=record['CategoryName'],
        channel_type=ChannelType(record['ChannelTypeId']).value,
        create_date=record['CreateDateUTC'],
        guild=guild,
        id=record['Id'],
        name=record['Name'],
        nsfw=record['NSFW'],
        update_date=record.get('UpdateDateUTC', None)
    )
    return channel
