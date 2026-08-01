import time, socket, subprocess, atexit, signal, threading, itertools
from queue import PriorityQueue, Empty
from typing import Optional
from concurrent.futures import Future

from .client import EngineClient

# ----------------- 命令注入队列（支持插队/间隔/重试） -----------------
class CommandInjector:
    """
    后台工作线程顺序发送命令：
      - inter_command_delay: 全局命令间隔（秒）
      - submit(): 普通入队
      - inject(): 立即插队（优先级更高）
      - cancel_all(): 取消尚未发送的任务
      - 可配置重试次数与回退
    返回 concurrent.futures.Future，可 .result() 阻塞拿回包。
    """

    def __init__(self,
                 client: EngineClient,
                 inter_command_delay: float = 0.2,
                 max_queue_size: int = 0,  # 0 表示不限制
                 retries: int = 1,
                 backoff: float = 0.5):
        self.client: EngineClient = client
        self.inter_command_delay: float = inter_command_delay
        self.retries: int = retries
        self.backoff: float = backoff

        self._q: PriorityQueue = PriorityQueue(maxsize=max_queue_size or 0)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._seq = itertools.count()
        self._last_sent = 0.0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear()
        self._thread = threading.Thread(target=self._worker, name="CommandInjector", daemon=True)
        self._thread.start()

    def stop(self, wait=True):
        self._stop.set()
        # 往队列塞个哨兵，唤醒阻塞
        try:
            self._q.put_nowait((999999, next(self._seq), None))
        except Exception:
            pass
        if wait and self._thread:
            self._thread.join(timeout=5)

    # —— 提交任务 —— #
    def submit(self, cmd: str, obj: Optional[dict] = None,
               *, timeout: Optional[float] = None,
               priority: int = 10) -> Future:
        """
        普通入队（priority 越小越靠前；inject 用的就是 priority=0）
        """
        fut = Future()
        task = (cmd, obj or {}, timeout, fut)
        self._q.put((priority, next(self._seq), task))
        return fut

    def inject(self, cmd: str, obj: Optional[dict] = None,
               *, timeout: Optional[float] = None) -> Future:
        """插队（最高优先级），用于“注入命令”"""
        return self.submit(cmd, obj, timeout=timeout, priority=0)

    def cancel_all(self):
        """取消尚未发送的任务（已发送中的不会取消）"""
        drained = []
        while True:
            try:
                drained.append(self._q.get_nowait())
            except Empty:
                break
        for _, _, task in drained:
            if task is None:  # 哨兵
                continue
            _, _, _, fut = task
            if not fut.done():
                fut.set_exception(RuntimeError("cancelled before send"))

    # —— 工作线程 —— #
    def _worker(self):
        while not self._stop.is_set():
            try:
                prio, seq, task = self._q.get(timeout=0.2)
            except Empty:
                continue
            if task is None:  # 哨兵
                continue

            cmd, obj, timeout, fut = task

            # 命令间隔限速
            now = time.time()
            gap = self.inter_command_delay - (now - self._last_sent)
            if gap > 0:
                time.sleep(gap)

            # 发送 + 重试
            try:
                result = self._send_with_retry(cmd, obj, timeout)
                if not fut.done():
                    fut.set_result(result)
            except Exception as e:
                if not fut.done():
                    fut.set_exception(e)
            finally:
                self._last_sent = time.time()

    def _send_with_retry(self, cmd: str, obj: dict, timeout: Optional[float]):
        tries, delay = 1 + max(0, self.retries), self.backoff
        last_exc = None
        for i in range(tries):
            try:
                return self.client.send_command(cmd, obj, timeout=timeout)
            except TimeoutError:
                # A receive timeout does not prove that the GUI command was not
                # accepted. Retrying load/slice can execute the same stateful
                # operation twice after the GUI thread becomes responsive.
                raise
            except (ConnectionError, socket.error) as e:
                last_exc = e
                # 尝试自动重连一次（send_command 内部已做；这里可多给点缓冲）
                try:
                    self.client._reconnect()
                except Exception:
                    pass
                if i < tries - 1:
                    time.sleep(delay)
                    delay *= 1.5
        raise last_exc or RuntimeError("send failed")
