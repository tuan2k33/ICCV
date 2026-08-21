import logging
from io import BytesIO

from fastapi.params import File

from app.core.app_status import AppStatus
from app.modules.tenant.repository import TenantRepository
from app.modules.tenant.schemas import TenantCreateSchema
from app.utils.response import error_exception_handler, handle_response
import pandas as pd

TEMPLATE_PATH = "template/information.xlsx"


class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    @staticmethod
    def _check_exist_task(tenant):
        if not tenant:
            raise error_exception_handler(AppStatus.ERROR_TENANT_NOT_FOUND)

    async def get_tenant_by_id(self, tenant_id: int):
        tenant = await self.tenant_repository.find_tenant_by_id(tenant_id=tenant_id)
        self._check_exist_task(tenant)
        return tenant

    async def get_settings_tenant_by_id(self, tenant_id: int):
        tenant = await self.tenant_repository.find_settings_tenant_by_id(tenant_id=tenant_id)
        return tenant

    async def get_information_tenant_by_id(self, tenant_id: int):
        tenant = await self.tenant_repository.find_information_tenant_by_id(tenant_id=tenant_id)
        return tenant

    async def create_tenant(self, tenant_data: TenantCreateSchema):
        tenant_data = tenant_data.model_dump(exclude_unset=True)
        await self.tenant_repository.create_tenant(tenant_data)
        return handle_response(app_status=AppStatus.TENANT_CREATED)

    async def update_tenant(self, tenant_id: int, tenant_data: dict):
        tenant = await self.tenant_repository.update_tenant(tenant_id=tenant_id, tenant_data=tenant_data)
        self._check_exist_task(tenant)
        return handle_response(app_status=AppStatus.TENANT_CREATED)

    async def update_settings_tenant(self, tenant_id: int, tenant_data: dict):
        """
        tenant_data = {
            "settings": {
                "reason": [{"label": "...", "value": "..."}]
            }
        }
        """
        tenant = await self.tenant_repository.update_settings_tenant(tenant_id=tenant_id,
                                                                     tenant_data=tenant_data)
        self._check_exist_task(tenant)
        return handle_response(app_status=AppStatus.TENANT_SETTING_UPDATED)

    async def update_information_tenant(self, tenant_id: int, tenant_data: dict):
        tenant = await self.tenant_repository.update_information_tenant(tenant_id=tenant_id,
                                                                        tenant_data=tenant_data)
        self._check_exist_task(tenant)
        return handle_response(app_status=AppStatus.TENANT_INFORMATION_UPDATED)

    async def import_template(self, tenant_id: int, content):

        data = pd.read_excel(BytesIO(content))

        result = {}
        reports = {}
        for index, row in data.iterrows():
            x = str(row.get("Double/Single Deep?")).upper()
            location = row.get("Location name")

            keys = str(location).split("-")
            idx = int(keys[1])
            key = f'{keys[0]}-{"odd" if idx % 2 != 0 else "even"}'
            if key not in result:
                result[key] = {}
            if key not in reports:
                reports[key] = []

            child_key = "-".join(keys[:2])
            if child_key not in result[key]:
                result[key][child_key] = {}
            reports[key].append({
                "day": keys[0],
                "Count": None,
                "Level": None,
                "Bin name": location,
                "Even/odd": idx % 2,
                "Material": None,
                "Pallet No": None,
                "Count sheet": None,
                "Material Description": None
            })

            result[key][child_key][location] = x if x in ['DOUBLE', 'SINGLE'] else None

        def sort_nested_dict(d):
            if isinstance(d, dict):
                return {k: sort_nested_dict(v) for k, v in sorted(d.items(), key=lambda x: x[0])}
            return d

        result = sort_nested_dict(result)
        temp_data = [{"tenant_id": tenant_id, "rack_name": key,
                      "report_task": sorted(value, key=lambda x: x.get("Bin name", ""))}
                     for key, value in reports.items()]
        data_update = {
            "information": {
                "racks": result,
            }}
        tenant = await self.tenant_repository.update_information_tenant(tenant_id=tenant_id,
                                                                        tenant_data=data_update)
        self._check_exist_task(tenant)
        return temp_data

    async def reload_temp_data(self, tenant_id: int, temp_data_service):
        logging.info(f"temp_data trống, tự động nạp lại từ {TEMPLATE_PATH}")
        try:
            with open(TEMPLATE_PATH, "rb") as f:
                content = f.read()
            temp_data = await self.import_template(tenant_id, content)
            await temp_data_service.bulk_insert_data(temp_data, tenant_id=tenant_id)
            logging.info(f"Nạp lại temp_data thành công: {len(temp_data)} racks")
            return temp_data
        except FileNotFoundError:
            logging.error(f"Không tìm thấy file template: {TEMPLATE_PATH}")
            return []
