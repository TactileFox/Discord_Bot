import requests as r
import unittest
from fastapi import HTTPException
from datetime import datetime as dt
from api.message_controller import get_message_by_id
from models.attachment import Attachment
from models.channel import Channel
from models.enums import ChannelType
from models.guild import Guild
from models.message import Message
from models.user import User
from models.user_mention import UserMention
from services.message_service import get_by_id as service_get_by_id
from unittest.mock import AsyncMock, patch


class TestMessages(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        cls.guild_id = 912345678999999999
        cls.channel_id = 6789123459999999999
        cls.attachment_id = 3456789129999999999
        cls.user_id = 123456789999999999
        cls.user_mention_id = 789123456999999999
        cls.message_id = 9999999999999999999

        cls.guild_record = {
            'Id': cls.guild_id,
            'Name': 'Mock guild name',
            'Description': 'Mock guild description',
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.guild_object = Guild(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            description='Mock guild description',
            id=cls.guild_id,
            name='Mock guild name',
            update_date=dt(2025, 1, 1, 1, 1, 2)
        )
        cls.channel_record = {
            'CategoryName': 'Mock channel category',
            'ChannelTypeId': 0,
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'GuildId': cls.guild_id,
            'Name': 'Mock channel name',
            'Id': cls.channel_id,
            'NSFW': 0,
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.channel_object = Channel(
            category='Mock channel category',
            channel_type=ChannelType(0).value,
            create_date=dt(2025, 1, 1, 1, 1, 1),
            guild=cls.guild_object,
            id=cls.channel_id,
            name='Mock channel name',
            nsfw=0,
            update_date=dt(2025, 1, 1, 1, 1, 2)
        )
        cls.attachment_records = [
            {
                'Id': cls.attachment_id,
                'Filename': 'Mock file name',
                'ContentType': 'Mock file type',
                'URL': 'Mock file url',
                'MessageId': cls.message_id,
                'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
                'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2),
                'DeleteDateUTC': None,
                'Deleted': 0
            },
            {
                'Id': cls.attachment_id,
                'Filename': 'Mock file name 2',
                'ContentType': 'Mock file type 2',
                'URL': 'Mock file url 2',
                'MessageId': cls.message_id,
                'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
                'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2),
                'DeleteDateUTC': None,
                'Deleted': 0
            }
        ]
        cls.attachment_objects = [
            Attachment(
                create_date=dt(2025, 1, 1, 1, 1, 1),
                delete_date=None,
                deleted=0,
                file_type='Mock file type',
                id=cls.attachment_id,
                message_id=cls.message_id,
                name='Mock file name',
                update_date=dt(2025, 1, 1, 1, 1, 2),
                url='Mock file url'
            ),
            Attachment(
                create_date=dt(2025, 1, 1, 1, 1, 1),
                delete_date=None,
                deleted=0,
                file_type='Mock file type 2',
                id=cls.attachment_id,
                message_id=cls.message_id,
                name='Mock file name 2',
                update_date=dt(2025, 1, 1, 1, 1, 2),
                url='Mock file url 2'
            )
        ]
        cls.user_record = {
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'Id': cls.user_id,
            'Username': 'Mock user username',
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.user_object = User(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            id=cls.user_id,
            update_date=dt(2025, 1, 1, 1, 1, 2),
            username='Mock user username'
        )
        cls.user_mention_records = [
            {
                'Id': cls.user_mention_id,
                'MessageId': cls.message_id,
                'AuthorId': cls.user_id,
                'RecipientId': cls.user_id,
                'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
                'DeleteDateUTC': None,
                'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2),
                'Deleted': 0
            },
            {
                'Id': cls.user_mention_id,
                'MessageId': cls.message_id,
                'AuthorId': cls.user_id,
                'RecipientId': cls.user_id,
                'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
                'DeleteDateUTC': None,
                'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2),
                'Deleted': 0
            }
        ]
        cls.user_mention_objects = [
            UserMention(
                author_id=cls.user_id,
                create_date=dt(2025, 1, 1, 1, 1, 1),
                delete_date=None,
                deleted=0,
                id=cls.user_mention_id,
                message_id=cls.message_id,
                update_date=dt(2025, 1, 1, 1, 1, 2),
                recipient=cls.user_object.model_copy(
                    update={'username': 'Mock recipient one'}
                )
            ),
            UserMention(
                author_id=cls.user_id,
                create_date=dt(2025, 1, 1, 1, 1, 1),
                delete_date=None,
                deleted=0,
                id=cls.user_mention_id,
                message_id=cls.message_id,
                update_date=dt(2025, 1, 1, 1, 1, 2),
                recipient=cls.user_object.model_copy(
                    update={'username': 'Mock recipient two'}
                )
            )
        ]
        cls.message_record = {
            'Id': cls.message_id,
            'UserId': cls.user_id,
            'GuildId': cls.guild_id,
            'Content': 'Mock message content',
            'ChannelId': cls.channel_id,
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2),
            'DeleteDateUTC': None,
            'Deleted': 0,
            'Edited': 1
        }
        cls.message_object = Message(
            attachments=cls.attachment_objects,
            author=cls.user_object,
            channel=cls.channel_object,
            content='Mock message content',
            create_date=dt(2025, 1, 1, 1, 1, 1),
            delete_date=None,
            deleted=0,
            edited=1,
            id=cls.message_id,
            update_date=dt(2025, 1, 1, 1, 1, 2),
            user_mentions=cls.user_mention_objects
        )

    # Verify API is running and fails 404
    async def test_connection(self):
        response = r.get(
            'http://127.0.0.1:8000/messages/1'
        )
        self.assertEqual(response.status_code, 404)

    # message_service.get_by_id() fail due to no message data found
    async def test_get_by_id_no_message_data_fail(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await service_get_by_id(mock_conn, self.message_id)

        self.assertEqual(result, None)
        mock_conn.fetchrow.assert_awaited_once_with(
            'SELECT * FROM "Message" WHERE "Id" = $1', self.message_id
        )

    # message_service.get_by_id() fail due to no author data found
    @patch(
        'services.message_service.user_service.get_by_id',
        new_callable=AsyncMock
    )
    async def test_get_by_id_no_author_data_fail(self, mock_get_user_by_id):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.message_record

        mock_get_user_by_id.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            await service_get_by_id(mock_conn, self.message_id)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(
            ctx.exception.detail, f'User {self.user_id} not found'
        )
        mock_conn.fetchrow.assert_awaited_once()
        mock_get_user_by_id.assert_awaited_once_with(
            mock_conn, self.user_id
        )

    # message_service.get_by_id() fail due to no channel data found
    @patch(
        'services.message_service.channel_service.get_by_id',
        new_callable=AsyncMock
    )
    @patch('services.message_service.get_user_by_id')
    async def test_get_by_id_no_channel_data_fail(
        self, mock_get_user_by_id, mock_get_channel_by_id
    ):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.message_record

        mock_get_user_by_id.return_value = self.user_object
        mock_get_channel_by_id.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            await service_get_by_id(mock_conn, self.message_id)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(
            ctx.exception.detail, f'Channel {self.channel_id} not found'
        )
        mock_get_user_by_id.assert_awaited_once_with(mock_conn, self.user_id)
        mock_get_channel_by_id.assert_awaited_once_with(
            mock_conn, self.channel_id
        )

    # message_service.get_by_id success with no user mentions or attachments
    @patch(
        'services.message_service.channel_service.get_by_id',
        new_callable=AsyncMock
    )
    @patch('services.message_service.get_user_by_id')
    @patch('services.message_service.user_mention_service.get_by_message_id')
    @patch('services.message_service.attachment_service.get_by_message_id')
    async def test_get_by_id_no_mentions_attachments_success(
        self, mock_get_user_mention, mock_get_attachments,
        mock_get_user_by_id, mock_get_channel_by_id
    ):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.message_record

        mock_get_user_by_id.return_value = self.user_object
        mock_get_channel_by_id.return_value = self.channel_object

        mock_get_user_mention.return_value = None
        mock_get_attachments.return_value = None

        expected_result = self.message_object.model_copy(
            update={
                'user_mentions': None,
                'attachments': None
            }
        )

        result = await service_get_by_id(mock_conn, self.message_id)

        self.assertEqual(result, expected_result)
        mock_conn.fetchrow.assert_awaited_once()
        mock_get_user_by_id.assert_awaited_once()
        mock_get_channel_by_id.assert_awaited_once()
        mock_get_user_mention.assert_awaited_once_with(
            mock_conn, self.message_id
        )
        mock_get_attachments.assert_awaited_once_with(
            mock_conn, self.message_id
        )

    # message_service.get_by_id success with user mentions and attachments
    @patch(
        'services.message_service.channel_service.get_by_id',
        new_callable=AsyncMock
    )
    @patch('services.message_service.get_user_by_id')
    @patch('services.message_service.user_mention_service.get_by_message_id')
    @patch('services.message_service.attachment_service.get_by_message_id')
    async def test_get_by_id_with_mentions_attachments_success(
        self,
        mock_get_attachments, mock_get_user_mention,
        mock_get_user_by_id, mock_get_channel_by_id
    ):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.message_record

        mock_get_user_by_id.return_value = self.user_object
        mock_get_channel_by_id.return_value = self.channel_object

        mock_get_user_mention.return_value = self.user_mention_objects
        mock_get_attachments.return_value = self.attachment_objects

        result = await service_get_by_id(mock_conn, self.message_id)

        self.assertEqual(result, self.message_object)
        mock_conn.fetchrow.assert_awaited_once()
        mock_get_user_by_id.assert_awaited_once()
        mock_get_channel_by_id.assert_awaited_once()
        mock_get_user_mention.assert_awaited_once()
        mock_get_attachments.assert_awaited_once()

    # messages/{id} 404
    @patch(
        'api.message_controller.message_service.get_by_id',
        new_callable=AsyncMock
    )
    @patch('api.message_controller.acquire_connection')
    async def test_controller_get_by_id_404(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = None
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        with self.assertRaises(HTTPException) as ctx:
            await get_message_by_id(self.message_id)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(
            ctx.exception.detail,
            f'Message {self.message_id} not found'
        )
        mock_get_by_id.assert_awaited_once_with(mock_conn, self.message_id)

    # messages/{id} 200
    @patch(
        'api.message_controller.message_service.get_by_id',
        new_callable=AsyncMock
    )
    @patch('api.message_controller.acquire_connection')
    async def test_controller_get_by_id_200(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = self.message_object
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        result = await get_message_by_id(self.message_id)

        self.assertEqual(result, self.message_object)
        mock_get_by_id.assert_awaited_once_with(mock_conn, self.message_id)
