"""
简化的并发控制系统
解决多用户并发访问问题
"""

import asyncio
import time
import uuid
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SimpleTaskQueue:
    """简化的任务队列，用于控制并发"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.running_tasks: Dict[str, dict] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.lock = asyncio.Lock()
    
    async def execute_task(self, task_func, *args, **kwargs):
        """执行任务，控制并发数量"""
        task_id = str(uuid.uuid4())
        
        # 获取信号量
        async with self.semaphore:
            async with self.lock:
                self.running_tasks[task_id] = {
                    "id": task_id,
                    "status": "running",
                    "start_time": time.time(),
                    "user_id": kwargs.get("user_id", "anonymous")
                }
            
            try:
                logger.info(f"Starting task {task_id}, concurrent tasks: {len(self.running_tasks)}")
                
                # 执行任务
                result = await task_func(*args, **kwargs)
                
                async with self.lock:
                    if task_id in self.running_tasks:
                        self.running_tasks[task_id]["status"] = "completed"
                        self.running_tasks[task_id]["end_time"] = time.time()
                
                logger.info(f"Task {task_id} completed successfully")
                return result
                
            except Exception as e:
                async with self.lock:
                    if task_id in self.running_tasks:
                        self.running_tasks[task_id]["status"] = "failed"
                        self.running_tasks[task_id]["error"] = str(e)
                        self.running_tasks[task_id]["end_time"] = time.time()
                
                logger.error(f"Task {task_id} failed: {e}")
                raise
                
            finally:
                # 清理完成的任务
                await asyncio.sleep(1)  # 短暂延迟，让状态查询有时间看到完成状态
                async with self.lock:
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]
    
    def get_status(self):
        """获取队列状态"""
        return {
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent,
            "available_slots": self.max_concurrent - len(self.running_tasks),
            "tasks": list(self.running_tasks.values())
        }
    
    def get_task_status(self, task_id: str):
        """获取特定任务状态"""
        return self.running_tasks.get(task_id)

# 全局队列实例
_simple_queue = None

def get_simple_queue() -> SimpleTaskQueue:
    """获取全局队列实例"""
    global _simple_queue
    if _simple_queue is None:
        _simple_queue = SimpleTaskQueue(max_concurrent=3)
    return _simple_queue

async def execute_with_queue(task_func, *args, **kwargs):
    """使用队列执行任务"""
    queue = get_simple_queue()
    return await queue.execute_task(task_func, *args, **kwargs)

def get_queue_status():
    """获取队列状态"""
    queue = get_simple_queue()
    return queue.get_status()
