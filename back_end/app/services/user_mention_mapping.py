from asyncpg import Record
from models.user import User
from models.user_mention import UserMention


def map_user_mention_row(record: Record, recipient: User) -> UserMention:
    user_mention = UserMention(
        author_id=record['AuthorId'],
        create_date=record['CreateDateUTC'],
        delete_date=record.get('DeleteDateUTC', None),
        deleted=record['Deleted'],
        id=record['Id'],
        message_id=record['MessageId'],
        update_date=record.get('UpdateDateUTC', None),
        recipient=recipient
    )
    return user_mention
