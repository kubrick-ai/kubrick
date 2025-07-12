from typing import Dict, Optional, List
from task import Task

class TaskStore:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def create_task(self, video_url: str) -> Task:
        task = Task(video_url)
        self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self, page: int = 1, page_limit: int = 10) -> List[Task]:
        start = (page - 1) * page_limit
        end = start + page_limit
        return list(self._tasks.values())[start:end]

    # This delete function isn't being used atm, but in case future implementation
    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
