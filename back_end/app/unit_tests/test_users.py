import requests as r
import unittest
from fastapi import HTTPException
from datetime import datetime as dt
from api.user_controller import get_user_by_id
from unittest.mock import AsyncMock, patch
from models.user import User
from services.user_service import get_by_id as service_get_by_id


class TestGuilds(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):  # Runs once at start
        cls.updated_user = User(
            create_date=dt(2025, 1, 1, 1, 1, 1),
            id=999999999999999999,
            update_date=dt(2025, 1, 1, 1, 1, 2),
            username='Mock user username'
        )
        cls.user_record_updated = {
            'CreateDateUTC': dt(2025, 1, 1, 1, 1, 1),
            'Id': 999999999999999999,
            'Username': 'Mock user username',
            'UpdateDateUTC': dt(2025, 1, 1, 1, 1, 2)
        }

    # Verify API is running and fails 404
    async def test_connection(self):
        response = r.get(
            'http://127.0.0.1:8000/users/1'
        )
        assert response.status_code == 404

    # user_service.get_by_id() fail due to no user data found
    async def test_get_by_id_no_user_data_fail(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None

        result = await service_get_by_id(mock_conn, 1)

        self.assertEqual(result, None)
        mock_conn.fetchrow.assert_awaited_once_with(
            'SELECT * FROM "User" WHERE "Id" = $1', 1
        )

    # user_service.get_by_id() success
    async def test_get_by_id_success(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = self.user_record_updated

        result = await service_get_by_id(mock_conn, 1)

        self.assertEqual(result, self.updated_user)
        mock_conn.fetchrow.assert_awaited_once()

    # users/{id} 404
    @patch('services.user_service.get_by_id', new_callable=AsyncMock)
    @patch('api.user_controller.acquire_connection')
    async def test_controller_get_by_id_404(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = None
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        with self.assertRaises(HTTPException) as ctx:
            await get_user_by_id(1)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "User 1 not found")
        mock_get_by_id.assert_awaited_once_with(mock_conn, 1)

    # users/{id} 200
    @patch('services.user_service.get_by_id', new_callable=AsyncMock)
    @patch('api.user_controller.acquire_connection')
    async def test_controller_get_by_id_200(
        self, mock_acquire_conn, mock_get_by_id
    ):
        mock_get_by_id.return_value = self.updated_user
        mock_conn = AsyncMock()
        mock_acquire_conn.return_value.__aenter__.return_value = mock_conn

        result = await get_user_by_id(1)

        self.assertEqual(result, self.updated_user)
        mock_get_by_id.assert_awaited_once()
