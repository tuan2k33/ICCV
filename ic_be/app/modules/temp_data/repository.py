from app.utils.sql_builder import SQLBuilder


class TempDataRepository:
    def __init__(self, db):
        self.db = db
        self.json_fields = {"result_e", "report_task"}

    def query(self):
        return SQLBuilder('temp_data', self.json_fields)

    async def get_temp_data_by_tenant(self, tenant_id):
        q, p = self.query().select("rack_name", "result_e", "report_task", "tenant_id", "total_progress").where(
            tenant_id=tenant_id).build()
        await self.db.execute(q, p)
        return await self.db.fetchall()

    async def bulk_insert_temp_data(self, data):
        q, p = self.query().bulk_insert(data).build()
        await self.db.execute(q, p)
        return await self.db.fetchall()

    async def update_temp_data_with_cond(self, data_update: dict, cond: dict):
        q, p = self.query().update(**data_update).where(**cond).build()
        await self.db.execute(q, p)
        return await self.db.fetchone()

    async def delete_temp_data_by_tenant_id(self, tenant_id: int):
        q, p = self.query().delete().where(tenant_id=tenant_id).build()
        await self.db.execute(q, p)
        return await self.db.fetchall()

    async def find_temp_by_rack_name(self, rack_name: str, tenant_id: int):
        q, p = self.query().select("rack_name", "result_e", "report_task", "tenant_id", "total_progress").where(
            rack_name=rack_name, tenant_id=tenant_id).build()
        await self.db.execute(q, p)
        return await self.db.fetchone()
