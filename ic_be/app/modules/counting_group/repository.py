from app.utils.sql_builder import SQLBuilder


class CountingGroupRepository:
    def __init__(self, db):
        self.db = db

    def query(self):
        return SQLBuilder("counting_groups")

    async def find_counting_group_by_batch_id(self, batch_id: int) -> list:
        q, p = self.query().where(batch_id=batch_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def find_racks_by_batch_id(self, batch_id: int) -> list:
        q, p = self.query().select('code', 'racks').where(batch_id=batch_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def bulk_insert_counting_group(self, counting_group_data: list):
        q, p = self.query().bulk_insert(counting_group_data).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def delete_counting_group(self, counting_group_id: list):
        q, p = self.query().delete().where(id__in=counting_group_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def delete_counting_group_by_batch_id(self, batch_id: int):
        q, p = self.query().delete().where(batch_id=batch_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def create_counting_group(self, counting_group_data: dict):
        q, p = self.query().insert(**counting_group_data).build()
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def get_counting_group_by_id(self, counting_group_id: int):
        q, p = self.query().select().where(id=counting_group_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def get_counting_by_user_id(self, batch_id: int, user_id: int):
        q, p = self.query().select().where(batch_id=batch_id).where_or(user_id_2=user_id, user_id_1=user_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def update_counting_group(self, counting_group_id: int, counting_group_data: dict):
        q, p = (self.query().
                update(**counting_group_data).
                where(id=counting_group_id).
                returning("id", 'user_id_1', 'user_id_2', "batch_id", "racks").build())
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def update_info_counting_group(self, counting_group_id: int, counting_group_data: dict):
        q, p = (self.query().
                update(**counting_group_data).
                where(id=counting_group_id).build()
                )
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def get_one_counting_group_field_none(self, field: str, batch_id: int):
        q, p = (self.query().
                select("id").
                where(batch_id=batch_id).
                where_raw(f"{field} IS NULL").limit(1).build()
                )
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def get_latest_counting_group(self, batch_id: int):
        q, p = (self.query().
                select("id", "code").
                where(batch_id=batch_id).
                order_by("id", "DESC").
                limit(1).build()
                )
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def update_by_cond(self, data_update: dict, condition: dict):
        q, p = (self.query().
                update(**data_update).returning("id", 'user_id_1', 'user_id_2', "batch_id", "racks").
                where(**condition).build()
                )
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    def build_move_rack_sql(self, from_id: int, to_id: int, rack_name: str):
        # step 1: check rack in from group
        check_from, p1 = (
            self.query()
            .select("id", "racks")
            .where_raw(f"%s = ANY(racks)", (rack_name,))
            .where(id=from_id)
            .build()
        )

        # step 2: remove rack from from_id
        remove_rack, p2 = (
            self.query()
            .update_raw("racks = array_remove(racks, %s)", [rack_name])  # dùng raw
            .where(id=from_id)
            .returning("id")
            .build()
        )
        # step 3: add rack to to_id
        add_rack, p3 = (
            self.query()
            .update_raw("racks = array_append(racks, %s)", [rack_name])
            .where(id=to_id)
            .returning("id", "user_id_1", "user_id_2", "batch_id")
            .build()
        )

        return {
            "check_from": (check_from, p1),
            "remove_rack": (remove_rack, p2),
            "add_rack": (add_rack, p3)
        }

    async def procedure_move_rack(self, from_id: int, to_id: int, rack_name: str):
        sqls = self.build_move_rack_sql(from_id, to_id, rack_name)
        # step 1: check rack in from group
        await self.db.execute(*sqls["check_from"])
        check_from = await self.db.fetchone()
        if not check_from:
            return None
        # step 2: remove rack from from_id
        await self.db.execute(*sqls["remove_rack"])
        remove_rack = await self.db.fetchone()
        if not remove_rack:
            return None
        # step 3: add rack to to_id
        await self.db.execute(*sqls["add_rack"])
        add_rack = await self.db.fetchone()
        if not add_rack:
            return None
        return {
            "from_group": check_from,
            "to_group": add_rack
        }
