import asyncpg as psy
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

pool: Optional[psy.pool.Pool] = None


async def connect_to_db(dsn: str):
    global pool
    if not pool:
        pool = await psy.create_pool(dsn)


async def disconnect_db():
    if pool:
        await pool.close()


@asynccontextmanager
async def acquire_connection() -> AsyncGenerator[psy.Connection, None]:
    if not pool:
        raise RuntimeError('Connection Pool not initialized')
    async with pool.acquire() as conn:
        yield conn
