from asyncpg import Record
from models.attachment import Attachment


def map_attachment_row(record: Record) -> Attachment:
    attachment = Attachment(
        create_date=record['CreateDateUTC'],
        delete_date=record.get('DeleteDateUTC', None),
        deleted=record['Deleted'],
        file_type=record['ContentType'],
        id=record['Id'],
        message_id=record['MessageId'],
        name=record['Filename'],
        update_date=record.get('UpdateDateUTC', None),
        url=record['URL']
    )
    return attachment
