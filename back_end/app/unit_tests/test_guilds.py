import requests as r
import unittest
from fastapi import HTTPException
from datetime import datetime as dt
from api.guild_controller import get_guild_by_id
from unittest.mock import AsyncMock, patch, MagicMock
from models.guild import Guild
from services.guild_service import get_by_id as service_get_by_id


class TestGuilds(unittest.IsolatedAsyncioTestCase):

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

    # Verify API is running and fails 404
    async def test_connection(self):
        response = r.get(
            'http://127.0.0.1:8000/guilds/1'
        )
        assert response.status_code == 404

    # guild_service.get_by_id() fail due to no guild data found
    async def test_get_by_id_no_guild_data_fail(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await service_get_by_id(mock_conn, 1)

        self.assertEqual(result, None)
        mock_conn.fetchrow.assert_awaited_once_with(
            'SELECT * FROM "Guild" WHERE "Id" = $1', 1
        )

    # guild_service.get_by_id() success
    @patch('services.guild_service.map_guild_row', new_callable=MagicMock)
    async def test_get_by_id_guild_and_guild_updated_success(
        self, mock_guild_mapper
    ):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.guild_record_updated
        mock_guild_mapper.return_value = self.updated_guild

        result = await service_get_by_id(mock_conn, 1)

        self.assertEqual(result, self.updated_guild)
        self.assertEqual(type(result), Guild)
        mock_conn.fetchrow.assert_awaited_once()
        mock_guild_mapper.assert_called_once_with(self.guild_record_updated)

    # guilds/{id} 404
    @patch('services.guild_service.get_by_id', new_callable=AsyncMock)
    @patch('api.guild_controller.acquire_connection')
    async def test_controller_get_by_id_404(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = None
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        with self.assertRaises(HTTPException) as ctx:
            await get_guild_by_id(1)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Guild 1 not found")
        mock_get_by_id.assert_awaited_once_with(mock_conn, 1)

    # guilds/{id} 200
    @patch('services.guild_service.get_by_id', new_callable=AsyncMock)
    @patch('api.guild_controller.acquire_connection')
    async def test_controller_get_by_id_200(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = self.updated_guild
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        result = await get_guild_by_id(1)

        self.assertEqual(result, self.updated_guild)
        mock_get_by_id.assert_awaited_once()
