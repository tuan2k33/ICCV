from app.modules.batch.schemas import BatchStatus
from app.utils.sql_builder import SQLBuilder


class BatchRepository:
    """
    Repository for managing batch operations.
    """

    def __init__(self, db):
        self.db = db
        self.query = SQLBuilder("batches")

    async def count_batches(self):
        """
        Count the total number of batches in the database.
        """
        query, _ = self.query.count().build()
        await self.db.execute(query, )
        result = await self.db.fetchone()
        return result.get("count", 0) if result else 0

    async def create_batch(self, batch_data):
        """
        Create a new batch in the database.
        """

        query, param = (self.query.
                        returning("id", 'code', 'status').
                        insert(**batch_data).build())
        await self.db.execute(query, param)
        result = await self.db.fetchone()
        return result

    async def get_batch(self, batch_id):
        """
        Retrieve a batch by its ID.
        """
        query, param = self.query.select().where(id=batch_id).build()
        await self.db.execute(query, param)
        result = await self.db.fetchone()
        return result

    async def get_batches(self, skip: int = 0, limit: int = 10):
        """
        Retrieve a list of batches with pagination.
        """
        query, param = SQLBuilder("batches").select().offset(skip).limit(limit).order_by('created_at').build()
        await self.db.execute(query, param)
        result = await self.db.fetchall()
        return result

    async def update_batch(self, batch_id, batch_data):
        """
        Update an existing batch.
        """
        query, param = self.query.update(**batch_data).where(id=batch_id).returning("status").build()
        await self.db.execute(query, param)
        result = await self.db.fetchone()
        return result

    async def delete_batch(self, batch_id):
        """
        Delete a batch by its ID.
        """
        query, param = self.query.delete().where(id=batch_id).build()
        await self.db.execute(query, param)
        return {"message": "Batch deleted successfully"}

    async def get_active_batch(self, tenant_id: int) -> int | None:
        """
        Get batch by active tenant ID.
        """
        query, param = self.query.select("id").where(tenant_id=tenant_id, status=BatchStatus.ACTIVE).limit(1).build()
        await self.db.execute(query, param)
        result = await self.db.fetchone()
        return result.get("id", None) if result else None
