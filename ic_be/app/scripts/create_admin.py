import asyncio
import argparse
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from passlib.context import CryptContext

from app.core.setting import settings

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin(username: str, email: str, password: str, roles: list[str]= ["ADMIN"]):
    async with AsyncConnectionPool(settings.DATABASE_URL, min_size=1, max_size=5) as pool:
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # Check nếu user đã tồn tại
                await cur.execute(
                    "SELECT * FROM users WHERE username = %s OR email = %s",
                    (username, email)
                )
                existing = await cur.fetchone()
                if existing:
                    print("⚠️ Admin đã tồn tại:", existing)
                    return

                # Hash password
                hashed_password = pwd_context.hash(password)

                # Insert user
                await cur.execute(
                    """
                    INSERT INTO users (username, email, password, roles, tenant_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, email, roles
                    """,
                    (username, email, hashed_password, roles, 1)
                )
                new_user = await cur.fetchone()
                await conn.commit()
                print("✅ Admin created:", new_user)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", required=True, help="Username of the admin")
    parser.add_argument("--email", required=True, help="Email of the admin")
    parser.add_argument("--password", required=True, help="Password of the admin")

    args = parser.parse_args()

    asyncio.run(create_admin(args.username, args.email, args.password))
