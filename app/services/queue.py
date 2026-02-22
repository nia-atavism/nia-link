"""
Nia-Link Task Queue v0.9
輕量非同步任務佇列 - 基於 asyncio.Queue
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger("nia-link.queue")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskQueue:
    """
    輕量非同步任務佇列
    
    特性：
    - 基於 asyncio.Queue，無需 Redis/Celery
    - 支援佇列大小限制與拒絕
    - 支援任務超時
    - 提供佇列狀態查詢
    """
    
    _instance = None
    
    def __new__(cls, max_size: int = 100):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_size: int = 100):
        if self._initialized:
            return
        self._initialized = True
        self._queue = asyncio.Queue(maxsize=max_size)
        self._max_size = max_size
        self._workers_started = False
        self._results: Dict[str, Dict] = {}
        self._task_counter = 0
        self._completed_count = 0
        self._failed_count = 0
    
    def _generate_task_id(self) -> str:
        self._task_counter += 1
        return f"task-{int(time.time())}-{self._task_counter}"
    
    async def submit(self, coro_func: Callable, *args, timeout: int = 60, **kwargs) -> str:
        """
        提交任務到佇列
        
        Returns:
            task_id 用於查詢結果
            
        Raises:
            asyncio.QueueFull: 佇列已滿
        """
        task_id = self._generate_task_id()
        
        task_info = {
            "id": task_id,
            "func": coro_func,
            "args": args,
            "kwargs": kwargs,
            "timeout": timeout,
            "status": TaskStatus.PENDING,
            "submitted_at": time.time(),
            "result": None,
            "error": None
        }
        
        self._results[task_id] = task_info
        
        try:
            self._queue.put_nowait(task_info)
            logger.info(f"Task {task_id} submitted, queue size: {self._queue.qsize()}")
        except asyncio.QueueFull:
            task_info["status"] = TaskStatus.FAILED
            task_info["error"] = "Queue is full"
            raise
        
        # 確保 worker 在運行
        if not self._workers_started:
            self._workers_started = True
            asyncio.create_task(self._worker())
        
        return task_id
    
    async def _worker(self):
        """背景 worker，持續處理佇列中的任務"""
        while True:
            try:
                task_info = await self._queue.get()
                task_id = task_info["id"]
                
                task_info["status"] = TaskStatus.RUNNING
                logger.info(f"Processing task {task_id}")
                
                try:
                    result = await asyncio.wait_for(
                        task_info["func"](*task_info["args"], **task_info["kwargs"]),
                        timeout=task_info["timeout"]
                    )
                    task_info["status"] = TaskStatus.COMPLETED
                    task_info["result"] = result
                    self._completed_count += 1
                except asyncio.TimeoutError:
                    task_info["status"] = TaskStatus.TIMEOUT
                    task_info["error"] = f"Task timed out after {task_info['timeout']}s"
                    self._failed_count += 1
                except Exception as e:
                    task_info["status"] = TaskStatus.FAILED
                    task_info["error"] = str(e)
                    self._failed_count += 1
                finally:
                    task_info["completed_at"] = time.time()
                    self._queue.task_done()
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """查詢任務狀態"""
        info = self._results.get(task_id)
        if not info:
            return None
        return {
            "id": info["id"],
            "status": info["status"],
            "submitted_at": info["submitted_at"],
            "completed_at": info.get("completed_at"),
            "error": info.get("error")
        }
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """取得任務結果"""
        info = self._results.get(task_id)
        if info and info["status"] == TaskStatus.COMPLETED:
            return info["result"]
        return None
    
    def get_queue_status(self) -> Dict:
        """取得佇列整體狀態"""
        return {
            "queue_size": self._queue.qsize(),
            "max_size": self._max_size,
            "total_submitted": self._task_counter,
            "completed": self._completed_count,
            "failed": self._failed_count,
            "pending": self._queue.qsize()
        }
    
    def cleanup_old_results(self, max_age: int = 3600):
        """清理超過指定時間的結果"""
        now = time.time()
        to_delete = [
            tid for tid, info in self._results.items()
            if info.get("completed_at") and (now - info["completed_at"]) > max_age
        ]
        for tid in to_delete:
            del self._results[tid]
