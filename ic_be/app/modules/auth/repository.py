from app.constant.statements.user import UserStatements
from app.utils.sql_builder import SQLBuilder


class AuthRepository:
    def __init__(self, db):
        self.db = db

    def query(self):
        return SQLBuilder("users").where(is_active=True)

    async def __execute_single(self, query, params):
        await self.db.execute(query, params)
        return await self.db.fetchone()

    async def __execute_all(self, query, params):
        await self.db.execute(query, params)
        return await self.db.fetchall()

    async def find_user_by_username_or_email(self, username: str):
        query = UserStatements.FIND_USER_BY_USERNAME_OR_EMAIL
        await self.db.execute(query, (username, username))
        result = await self.db.fetchone()
        return result

    async def create_user(self, user_data: dict):
        q, p = self.query().insert(**user_data).returning('id', 'fullname').build()
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        return result

    async def create_users(self, users_data: list):
        q, p = self.query().bulk_insert(users_data).build()
        return await self.__execute_all(q, p)

    async def update_user(self, user_id, user_data: dict):
        query, param = self.query().update(**user_data).where(id=user_id).build()
        await self.db.execute(query, param)
        result = await self.db.fetchone()
        return result

    async def delete_user(self, user_id):
        query, param = self.query().delete().where(id=user_id).build()
        await self.db.execute(query, param)
        result = await self.db.fetchone()
        return result.get("id") if result else None

    async def delete_users(self, data_assign: list, conditions_set: list = None):
        q, p = self.query().bulk_update(data_assign, conditions_set).build()
        await self.db.execute(q, p)
        rows = await self.db.fetchall()
        return [r["id"] for r in rows] if rows else []

    async def exists_user(self, username: str, phone_number: str = None):
        query = UserStatements.EXISTS_USER
        await self.db.execute(query, (username, phone_number))
        result = await self.db.fetchone()
        return result.get("exists", False) if result else False

    async def find_user_by_id(self, user_id: str):
        q, p = self.query().select().where(id=user_id).build()
        await self.db.execute(q, p)
        result = await self.db.fetchone()
        del result["password"]
        return result

    async def __fetch_page_with_total_of_user(self, query, skip, limit):
        q, p = query.copy().select().order_by('created_at', 'DESC').offset(skip).limit(limit).build()
        users = await self.__execute_all(q, p)
        q, p = query.count().build()
        total = await self.__execute_single(q, p)
        return total.get('count'), users

    async def get_all_users(self, skip: int, limit: int, roles: list, user_data: dict):
        query = self.query().select('id', 'username', 'fullname', 'phone_number',
                                           'roles', 'company', 'created_at')
        if user_data:
            query = query.where(**user_data)
        if roles:
            query = query.where_raw("roles && %s", (roles,))
        return await self.__fetch_page_with_total_of_user(query, skip, limit)

    async def fetch_all_users(self, roles: list, user_data: dict):
        query = self.query().select('id', 'username', 'fullname', 'phone_number')
        if user_data:
            query = query.where(**user_data)
        if roles:
            query = query.where_raw("roles && %s", (roles,))
        q, p = query.build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def get_user_by_company(self, company: str, tenant_id: int, roles: list):
        q, p = self.query().select().where(company=company, tenant_id=tenant_id, roles=roles).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def count_users(self):
        query = UserStatements.COUNT_USERS
        await self.db.execute(query)
        result = await self.db.fetchone()
        return result.get("count", 0) if result else 0

    async def bulk_insert(self, data_insert: list):
        q, p = self.query().bulk_insert(data_insert).build()
        await self.db.execute(q, p)
        result = await self.db.fetchall()
        return result

    async def get_users_by_field(self, field: str, values: list, select_fields: list = None):
        if not values:
            return []
        select_fields = select_fields or [field]

        q, p = (
            self.query()
            .select(*select_fields)
            .where(**{f"{field}__in": values})
            .build()
        )

        await self.db.execute(q, p)
        return await self.db.fetchall()
