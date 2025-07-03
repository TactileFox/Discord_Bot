import requests as r
import unittest
from fastapi import HTTPException
from datetime import datetime as dt
from api.channel_controller import get_channel_by_id
from unittest.mock import AsyncMock, patch
from models.channel import Channel
from models.enums import ChannelType
from models.guild import Guild
from services.channel_service import get_by_id as service_get_by_id


class TestChannels(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):  # Runs once at start
        cls.guild_id = 912345678999999999
        cls.channel_id = 6789123459999999999
        cls.attachment_id = 3456789129999999999
        cls.user_id = 123456789999999999
        cls.user_mention_id = 789123456999999999
        cls.message_id = 9999999999999999999

        cls.unupdated_guild = Guild(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            description='Mock guild description',
            id=cls.guild_id,
            name='Mock guild name',
            update_date=None
        )
        cls.updated_guild = Guild(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            description='Mock guild description',
            id=cls.guild_id,
            name='Mock guild name',
            update_date=dt(2025, 1, 1, 1, 1, 2)
        )
        cls.unupdated_channel = Channel(
            category='Mock channel category',
            channel_type=ChannelType(0).value,
            create_date=dt(2025, 1, 1, 1, 1, 1),
            guild=cls.unupdated_guild,
            id=cls.channel_id,
            name='Mock channel name',
            nsfw=0,
            update_date=None
        )
        cls.updated_channel = Channel(
            category='Mock channel category',
            channel_type=ChannelType(0).value,
            create_date=dt(2025, 1, 1, 1, 1, 1),
            guild=cls.updated_guild,
            id=cls.channel_id,
            name='Mock channel name',
            nsfw=0,
            update_date=dt(2025, 1, 1, 1, 1, 2)
        )
        cls.channel_record_updated = {
            'CategoryName': 'Mock channel category',
            'ChannelTypeId': 0,
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'GuildId': cls.guild_id,
            'Name': 'Mock channel name',
            'Id': cls.channel_id,
            'NSFW': 0,
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.channel_record_unupdated = {
            'CategoryName': 'Mock channel category',
            'ChannelTypeId': 0,
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'GuildId': cls.guild_id,
            'Name': 'Mock channel name',
            'Id': cls.channel_id,
            'NSFW': 0,
            'UpdateDateUTC': None
        }
        cls.guild_record_updated = {
            'Id': cls.guild_id,
            'Name': 'Mock guild name',
            'Description': 'Mock guild description',
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.guild_record_unupdated = {
            'Id': cls.guild_id,
            'Name': 'Mock guild name',
            'Description': 'Mock guild description',
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'UpdateDateUTC': None
        }

    # Verify API is running and fails 404
    async def test_connection(self):
        response = r.get(
            'http://127.0.0.1:8000/Channels/1'
        )
        assert response.status_code == 404

    # channel_service.get_by_id() fail due to no channel data found
    async def test_get_by_id_no_channel_data_fail(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await service_get_by_id(mock_conn, self.channel_id)

        self.assertEqual(result, None)
        mock_conn.fetchrow.assert_awaited_once_with(
            'SELECT * FROM "Channel" WHERE "Id" = $1', self.channel_id
        )

    # channel_service.get_by_id() fail due to no guild data found
    @patch('services.guild_service.get_by_id', new_callable=AsyncMock)
    async def test_get_by_id_no_guild_data_fail(self, mock_guild_get_by_id):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.channel_record_unupdated
        mock_guild_get_by_id.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            await service_get_by_id(mock_conn, self.channel_id)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(
            ctx.exception.detail,
            f'Guild {self.guild_id} not found'
        )
        mock_conn.fetchrow.assert_awaited_once()
        mock_guild_get_by_id.assert_awaited_once_with(
            mock_conn, self.guild_id
        )

    # channel_service.get_by_id() success
    @patch('services.guild_service.get_by_id', new_callable=AsyncMock)
    async def test_get_by_id_channel_and_guild_updated_success(
        self, mock_guild_get_by_id
    ):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.channel_record_updated
        mock_guild_get_by_id.return_value = self.updated_guild

        result = await service_get_by_id(mock_conn, self.channel_id)

        self.assertEqual(result, self.updated_channel)
        self.assertEqual(type(result), Channel)
        mock_conn.fetchrow.assert_awaited_once()
        mock_guild_get_by_id.assert_awaited_once_with(
            mock_conn, self.guild_id
        )

    # channels/{id} 404
    @patch('services.channel_service.get_by_id', new_callable=AsyncMock)
    @patch('api.channel_controller.acquire_connection')
    async def test_controller_get_by_id_404(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = None
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        with self.assertRaises(HTTPException) as ctx:
            await get_channel_by_id(self.channel_id)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(
            ctx.exception.detail,
            f"Channel {self.channel_id} not found"
        )
        mock_get_by_id.assert_awaited_once_with(mock_conn, self.channel_id)

    # channels/{id} 200
    @patch('services.channel_service.get_by_id', new_callable=AsyncMock)
    @patch('api.channel_controller.acquire_connection')
    async def test_controller_get_by_id_200(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = self.updated_channel
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        result = await get_channel_by_id(self.channel_id)

        self.assertEqual(result, self.updated_channel)
        mock_get_by_id.assert_awaited_once()
