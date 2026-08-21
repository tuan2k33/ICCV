import random
from datetime import datetime
from io import BytesIO

import pandas as pd
from starlette.responses import StreamingResponse

from app.constant.enums import CompanyNameEnum
from app.core.app_status import AppStatus
from app.modules.counting_group.repository import CountingGroupRepository
from app.modules.task.repository import TaskRepository
from app.utils.response import error_exception_handler, handle_response


class CountingGroupService:

    def __init__(self, repo: CountingGroupRepository, task_repository: TaskRepository):
        self.repo = repo
        self.task_repository = task_repository

    @staticmethod
    def group_users(lst_users1, lst_users2):
        random.shuffle(lst_users1)
        random.shuffle(lst_users2)
        groups = []
        max_len = max(len(lst_users1), len(lst_users2))
        for i in range(max_len):
            group = {"code": f'{i + 1}'}
            if i < len(lst_users1):
                group['user_id_1'] = lst_users1[i].get('id')
                group['fullname_1'] = lst_users1[i].get('fullname', '')
            if i < len(lst_users2):
                group['user_id_2'] = lst_users2[i].get('id')
                group['fullname_2'] = lst_users2[i].get('fullname', '')
            groups.append(group)
        return groups

    @staticmethod
    def radom_rack_with_group(groups: list, racks: list):
        # eligible_groups = [group for group in groups if 'user_id_1' in group and 'user_id_2' in group]
        eligible_groups = groups
        random.shuffle(racks)
        if eligible_groups:
            racks_per_group = len(racks) // len(eligible_groups)  # Racks per eligible group
            remaining_racks = len(racks) % len(eligible_groups)  # Remaining racks after even distribution

            rack_index = 0
            for group in eligible_groups:
                # Assign a slice of racks to the group
                group_racks = racks[rack_index:rack_index + racks_per_group]
                rack_index += racks_per_group
                group['racks'] = group_racks

            # Distribute remaining racks (one by one) to the eligible groups
            for i in range(remaining_racks):
                eligible_groups[i]['racks'].append(racks[rack_index])
                rack_index += 1
        return groups

    async def random_counting_group(self, lst_users1, lst_users2, racks: list):
        groups_user = self.group_users(lst_users1, lst_users2)

        counting_group = self.radom_rack_with_group(groups_user, racks)
        return counting_group

    async def save_counting_group(self, counting_group: list, batch_id: int):
        counting_group = [{**groups_user, "batch_id": batch_id} for groups_user in counting_group]
        await self.repo.delete_counting_group_by_batch_id(batch_id)
        await self.repo.bulk_insert_counting_group(counting_group)
        result = []
        for group in counting_group:
            result.extend([{"rack_name": rack, "user_e": group.get('user_id_2') or 0  , "batch_id": batch_id,
                            "user_view_e": group.get('user_id_1') or 0} for rack in (group.get("racks") or [])])
        return result

    async def create_counting_group(self, data: dict):
        await self.repo.create_counting_group(data)

    async def find_counting_group_not_exist_user(self, batch_id: int):
        counting_group = await self.repo.find_counting_group_by_batch_id(batch_id)
        return counting_group

    async def change_user_in_group(self, data: dict):
        group = await self.repo.update_counting_group(data.get("id"), data)
        return group

    async def get_process(self, batch_id: int):
        tasks = await self.task_repository.get_completed_tasks(batch_id)
        racks = await self.repo.find_racks_by_batch_id(batch_id)

        result = await self.handle_data_process(tasks, racks)
        return result

    async def handle_data_process(self, data_origin: list, data_path: list):
        done_nodes = {d["rack_name"] for d in data_origin}
        results = {
            p["code"]: await self.handle_calc_percent(p["racks"], done_nodes)
            for p in data_path
        }
        return results

    @staticmethod
    async def handle_calc_percent(racks: list, done_nodes: set):
        done = sum(1 for n in racks if n in done_nodes)
        total = len(racks)
        return round(done / total * 100, 2) if total else 0

    async def get_counting_group(self, batch_id: int, convert_racks: bool = False):
        counting_group = await self.repo.find_counting_group_by_batch_id(batch_id)
        result = []
        if convert_racks:
            for group in counting_group:
                result.extend(
                    [{"code": group["code"], "rack_name": rack, "id": group.get("id")} for rack in
                     group.get("racks") or []])
            return result

        return counting_group

    async def get_group_by_id(self, group_id: int):
        group = await self.repo.get_counting_group_by_id(group_id)
        return group

    async def update_group_racks(self, group_id: int, new_racks: set, old_racks: set):
        deleted_racks = list(old_racks - new_racks)
        added_racks = list(new_racks - old_racks)
        group = await self.repo.update_counting_group(group_id, {"racks": list(new_racks)})
        return dict(
            group=group,
            deleted_racks=deleted_racks,
            added_racks=added_racks,
        )

    async def sync_group_racks(self, group_id: int, new_racks: list):
        group = await self.get_group_by_id(group_id)
        return await self.update_group_racks(group_id, set(new_racks), set(group.get("racks")))

    async def export_group_counting(self, batch_id: int):
        counting_group = await self.get_counting_group(batch_id)
        return await self.export_counting_group_to_excel(counting_group)

    async def move_rack_to_group(self, group_from_id, group_to_id, rack_name):
        result = await self.repo.procedure_move_rack(group_from_id, group_to_id, rack_name)
        if not result:
            raise error_exception_handler(AppStatus.ERROR_RACK_NOT_FOUND)

        return result["to_group"]

    async def export_counting_group_to_excel(self, data: list):
        """
        Export counting group ra Excel với format đẹp
        """
        if not data:
            return None

        for group in data:
            group['racks'] = str(", ".join(group.get('racks') or [])).replace("-even", " chẵn").replace("-odd", " lẻ")

        df = pd.DataFrame(data)

        column_mapping = {
            'code': 'Cặp',
            'fullname_1': 'Linfox',
            'fullname_2': 'Unilever',
            'racks': 'Dãy đếm',
        }
        columns_to_keep = [col for col in column_mapping.keys() if col in df.columns]
        df = df[columns_to_keep]
        df.rename(columns=column_mapping, inplace=True)

        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        filename = f"counting_group_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    async def create_or_update_user_into_counting_group(self, user_id, fullname, company: CompanyNameEnum,
                                                        batch_id: int):
        company_is_linfox = bool(company == CompanyNameEnum.LINFOX)

        user_field = "user_id_1" if company_is_linfox else "user_id_2"
        fullname_field = "fullname_1" if company_is_linfox else "fullname_2"
        group_odd = await self.repo.get_one_counting_group_field_none(user_field, batch_id)
        if not group_odd:
            latest_batch = await self.repo.get_latest_counting_group(batch_id)
            create_data = {
                "code": str(int(latest_batch["code"]) + 1),
                user_field: user_id,
                fullname_field: fullname,
                "batch_id": batch_id,
                "racks": [],
            }
            return await self.repo.create_counting_group(create_data), False
        else:
            update_data = {user_field: user_id, fullname_field: fullname}
            group = await self.repo.update_counting_group(group_odd.get("id"), update_data)
            return group, True
