from app.modules.task.schemas import TaskCreateSchema


class DistributeTask:
    """
    DistributeTask class is responsible for distributing tasks to workers.
    It manages the task distribution process and ensures that tasks are
    assigned to the appropriate workers based on their availability and
    capabilities.
    """

    def __init__(self, batch_id, task_service, temp_data):
        self.batch_id = batch_id
        self.task_service = task_service
        self.temp_data = temp_data

    async def excuse(self):
        """
        Excuse method is used to handle any exceptions that occur during
        the task distribution process. It can be overridden in derived classes
        to provide custom exception handling logic.
        """
        tasks = self.germinate_task()
        if not tasks:
            return []
        return await self.task_service.create_tasks(tasks)

    def germinate_task(self) -> list:
        """
        Germinate task method is used to prepare the tasks for distribution.
        It can be overridden in derived classes to provide custom task
        preparation logic.
        """
        tasks = [
            TaskCreateSchema(**{**item, "result_e": item.get("result_e") or {}}, batch_id=self.batch_id).model_dump()
            for item in self.temp_data
        ]
        return tasks
