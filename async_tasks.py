"""
异步任务管理模块 - 使用线程池处理长时间运行的任务
"""
import threading
import uuid
from datetime import datetime
from typing import Dict, Callable, Any

class AsyncTaskManager:
    """管理异步任务的类"""

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def create_task(self, func: Callable, *args, **kwargs) -> str:
        """
        创建一个异步任务

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            task_id: 任务 ID
        """
        task_id = str(uuid.uuid4())

        with self.lock:
            self.tasks[task_id] = {
                'status': 'pending',
                'result': None,
                'error': None,
                'created_at': datetime.now().isoformat(),
                'completed_at': None
            }

        # 在后台线程中执行任务
        def run_task():
            try:
                with self.lock:
                    self.tasks[task_id]['status'] = 'running'

                result = func(*args, **kwargs)

                with self.lock:
                    self.tasks[task_id]['status'] = 'completed'
                    self.tasks[task_id]['result'] = result
                    self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            except Exception as e:
                with self.lock:
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['error'] = str(e)
                    self.tasks[task_id]['completed_at'] = datetime.now().isoformat()

        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态信息
        """
        with self.lock:
            if task_id not in self.tasks:
                return {
                    'status': 'not_found',
                    'error': f'Task {task_id} not found'
                }
            return self.tasks[task_id].copy()

    def get_result(self, task_id: str) -> Any:
        """
        获取任务结果（如果任务完成）

        Args:
            task_id: 任务 ID

        Returns:
            任务结果
        """
        with self.lock:
            if task_id not in self.tasks:
                raise ValueError(f'Task {task_id} not found')

            task = self.tasks[task_id]
            if task['status'] == 'completed':
                return task['result']
            elif task['status'] == 'failed':
                raise Exception(f"Task failed: {task['error']}")
            else:
                raise Exception(f"Task still {task['status']}")

# 全局任务管理器实例
task_manager = AsyncTaskManager()
