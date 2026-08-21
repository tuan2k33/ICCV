from app.modules.batch.schemas import BatchCreateSchema, BatchUpdateSchema


class BatchService:
    def __init__(self, batch_repository):
        self.batch_repository = batch_repository

    async def get_list(self, skip: int = 0, limit: int = 10):
        total = await self.batch_repository.count_batches()
        batches = await self.batch_repository.get_batches(skip, limit)
        return total, batches

    async def get_batch(self, batch_id: str):
        return await self.batch_repository.get_batch(batch_id)

    async def create_batch(self, batch_data: BatchCreateSchema, user_id):
        return await self.batch_repository.create_batch({**batch_data.__dict__, "created_by": user_id})

    async def update_batch(self, batch_id: str, batch_data: BatchUpdateSchema):
        return await self.batch_repository.update_batch(batch_id, batch_data.__dict__)

    async def delete_batch(self, batch_id: str):
        return await self.batch_repository.delete_batch(batch_id)

    async def get_active_batch(self, tenant_id: int):
        return await self.batch_repository.get_active_batch(tenant_id)
