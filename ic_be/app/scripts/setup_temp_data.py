import asyncio

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.setting import settings
from app.modules.temp_data.repository import TempDataRepository
from app.modules.temp_data.service import TempDataSevice
from app.modules.tenant.repository import TenantRepository
from app.modules.tenant.service import TenantService

TEMPLATE_PATH = "template/information.xlsx"
TENANT_ID = 1  # ID tenant bạn muốn auto setup


async def setup_temp_data():
    async with AsyncConnectionPool(settings.DATABASE_URL, min_size=1, max_size=5) as pool:
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                print("🚀 Starting setup temp data...")
                # 1. Mở file Excel
                with open(TEMPLATE_PATH, "rb") as f:
                    content = f.read()

                # 3. Khởi tạo service (inject repository)
                tenant_repo = TenantRepository(cur)
                temp_repe = TempDataRepository(cur)

                tenant_service = TenantService(tenant_repo)
                temp_data_service = TempDataSevice(temp_repe)

                # 4. Gọi import_template
                temp_data = await tenant_service.import_template(tenant_id=TENANT_ID, content=content)

                # 5. Gọi insert vào DB
                await temp_data_service.bulk_insert_data(temp_data, tenant_id=TENANT_ID)

                # 6. In kết quả
                print("✅ Temp data setup completed!")


def run():
    asyncio.run(setup_temp_data())


if __name__ == "__main__":
    run()
