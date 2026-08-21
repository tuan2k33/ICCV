from app.utils.sql_builder import SQLBuilder


class TenantRepository:
    def __init__(self, db):
        self.db = db
        self.query = SQLBuilder('tenants')

    async def __execute_single(self, query, params):
        await self.db.execute(query, params)
        return await self.db.fetchone()

    async def __execute_all(self, query, params):
        await self.db.execute(query, params)
        return await self.db.fetchall()

    async def find_tenant_by_id(self, tenant_id: int):
        q, p = self.query.select('id', 'name', 'banner').where(id=tenant_id).build()
        return await self.__execute_single(q, p)

    async def find_settings_tenant_by_id(self, tenant_id: int):
        q, p = self.query.select('settings').where(id=tenant_id).build()
        return await self.__execute_single(q, p)

    async def find_information_tenant_by_id(self, tenant_id: int):
        q, p = self.query.select('information').where(id=tenant_id).build()
        return await self.__execute_single(q, p)

    async def create_tenant(self, tenant_data: dict):
        q, p = self.query.insert(**tenant_data).build()
        return await self.__execute_single(q, p)

    async def update_tenant(self, tenant_id: int, tenant_data: dict):
        q, p = self.query.update(**tenant_data).where(id=tenant_id).build()
        result = await self.__execute_single(q, p)
        return result

    async def update_settings_tenant(self, tenant_id: int, tenant_data: dict):
        q, p = self.query.update(**tenant_data).where(id=tenant_id).returning('settings').build()
        result = await self.__execute_single(q, p)
        return result

    async def update_information_tenant(self, tenant_id: int, tenant_data: dict):
        q, p = self.query.update(**tenant_data).where(id=tenant_id).returning('id').build()
        result = await self.__execute_single(q, p)
        return result
