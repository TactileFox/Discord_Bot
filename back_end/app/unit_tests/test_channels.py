import requests as r
import unittest
from fastapi import HTTPException
from datetime import datetime as dt
from unittest.mock import AsyncMock, patch
from models.channel import Channel
from models.enums import ChannelType
from models.guild import Guild
from services.channel_service import get_by_id


class TestChannelService(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):  # Runs once at start
        cls.unupdated_guild = Guild(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            description='Mock guild description',
            id=999999999999999999,
            name='Mock guild name',
            update_date=None
        )
        cls.updated_guild = Guild(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            description='Mock guild description',
            id=999999999999999999,
            name='Mock guild name',
            update_date=dt(2025, 1, 1, 1, 1, 2)
        )
        cls.unupdated_channel = Channel(
            category='Mock channel category',
            channel_type=ChannelType(0).value,
            create_date=dt(2025, 1, 1, 1, 1, 1),
            guild=cls.unupdated_guild,
            id=9999999999999999999,
            name='Mock channel name',
            nsfw=0,
            update_date=None
        )
        cls.updated_channel = Channel(
            category='Mock channel category',
            channel_type=ChannelType(0).value,
            create_date=dt(2025, 1, 1, 1, 1, 1),
            guild=cls.updated_guild,
            id=9999999999999999999,
            name='Mock channel name',
            nsfw=0,
            update_date=dt(2025, 1, 1, 1, 1, 2)
        )
        cls.channel_record_updated = {
            'CategoryName': 'Mock channel category',
            'ChannelTypeId': 0,
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'GuildId': 999999999999999999,
            'Name': 'Mock channel name',
            'Id': 9999999999999999999,
            'NSFW': 0,
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.channel_record_unupdated = {
            'CategoryName': 'Mock channel category',
            'ChannelTypeId': 0,
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'GuildId': 999999999999999999,
            'Name': 'Mock channel name',
            'Id': 9999999999999999999,
            'NSFW': 0,
            'UpdateDateUTC': None
        }
        cls.guild_record_updated = {
            'Id': 999999999999999999,
            'Name': 'Mock guild name',
            'Description': 'Mock guild description',
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }
        cls.guild_record_unupdated = {
            'Id': 999999999999999999,
            'Name': 'Mock guild name',
            'Description': 'Mock guild description',
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'UpdateDateUTC': None
        }

    async def test_connection(self):
        response = r.get(
            'http://127.0.0.1:8000/Channels/1'
        )
        assert response.status_code == 404

    async def test_get_by_id_no_channel_data_404(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            await get_by_id(mock_conn, 1)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, 'Channel not found')
        mock_conn.fetchrow.assert_awaited_once_with(
            'SELECT * FROM "Channel" WHERE "Id" = $1', 1
        )

    @patch('services.guild_service.get_by_id', new_callable=AsyncMock)
    async def test_get_by_id_no_guild_data_404(self, mock_guild_get_by_id):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.channel_record_unupdated
        mock_guild_get_by_id.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            await get_by_id(mock_conn, 1)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, 'Guild not found')
        mock_conn.fetchrow.assert_awaited_once()
        mock_guild_get_by_id.assert_awaited_once_with(
            mock_conn, 999999999999999999
        )

    @patch('services.guild_service.get_by_id', new_callable=AsyncMock)
    async def test_get_by_id_channel_and_guild_updated_200(
        self, mock_guild_get_by_id
    ):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.channel_record_updated
        mock_guild_get_by_id.return_value = self.updated_guild

        result = await get_by_id(mock_conn, 1)

        self.assertEqual(result, self.updated_channel)
        self.assertEqual(type(result), Channel)
        mock_conn.fetchrow.assert_awaited_once()
        mock_guild_get_by_id.assert_awaited_once_with(
            mock_conn, 999999999999999999
        )
