from asyncpg import Record
from app.models.guild import Guild


def map_guild_row(record: Record) -> Guild:
    guild = Guild(
        id=record['Id'],
        description=record['Description'],
        name=record['Name'],
        create_date=record['CreateDateUTC'],
        update_date=record.get('UpdateDateUTC', None)
    )
    return guild
