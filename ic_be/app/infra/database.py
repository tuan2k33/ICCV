from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from app.core.setting import settings
from psycopg.rows import dict_row

async_pool: AsyncConnectionPool = None # Global variable to hold the async connection pool


@asynccontextmanager
async def lifespan(app):
    global async_pool
    # Use the pool as a context manager to avoid the deprecation warning
    async with AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            min_size=1,
            max_size=10,
    ) as pool:
        async_pool = pool
        yield


async def get_conn():
    async with async_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            yield cur
