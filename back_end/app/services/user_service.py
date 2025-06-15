from asyncpg import Connection
from app.models.user import User
from app.services.user_mapping import map_user_row


async def get_by_id(conn: Connection, id: int) -> User | None:
    user_data = conn.fetchrow('SELECT * FROM "User" WHERE "Id" = $1', id)
    if user_data:
        return map_user_row(user_data)
    return None
