import logging
from app.modules.temp_data.repository import TempDataRepository

logger = logging.getLogger(__name__)


class TempDataSevice:
    def __init__(self, repo: TempDataRepository):
        self.repo = repo

    async def bulk_insert_data(self, data: list, tenant_id):
        await self.repo.delete_temp_data_by_tenant_id(tenant_id)
        return await self.repo.bulk_insert_temp_data(data)

    async def get_temp_data_by_tenant_id(self, tenant_id):
        return await self.repo.get_temp_data_by_tenant(tenant_id)

    async def process_data_of_ai(self, data, rack_name, tenant_id):
        temp = await self.repo.find_temp_by_rack_name(rack_name, tenant_id)
        if not temp:
            logging.error(f"No temp data found for {tenant_id}: {rack_name}")
            return None
        result = temp.get('result_e') if temp.get('result_e') else {}
        new_result = {}
        for k, v in data.items():
            key = '-'.join(str(k).split("-", 2)[:2])
            new_result.setdefault(key, {})[k] = v

        for rack, items in new_result.items():
            for slot, fields in items.items():
                if rack in result and slot in result[rack]:
                    result[rack][slot].update(fields)
                else:
                    result.setdefault(rack, {})[slot] = fields

        task_data = {
            "result_e": result,
            "total_progress": sum(len(v) for v in result.values())
        }
        cond = {'rack_name': rack_name, "tenant_id": tenant_id}
        return await self.repo.update_temp_data_with_cond(task_data, cond)
