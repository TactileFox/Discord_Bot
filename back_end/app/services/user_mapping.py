from asyncpg import Record
from models.user import User


def map_user_row(record: Record) -> User:
    user = User(
        create_date=record['CreateDateUTC'],
        id=record['Id'],
        update_date=record.get('UpdateDateUTC', None),
        username=record['Username']
    )
    return user
