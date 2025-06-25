from __future__ import annotations

import threading
from queue import Queue
from typing import Callable
from abc import ABC, abstractmethod


class JobQueue(ABC):
    """Interface for job queues."""

    @abstractmethod
    def enqueue(self, func: Callable[[], None]) -> None:
        """Queue a job for execution."""

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanly shutdown the queue."""


class ThreadJobQueue(JobQueue):
    """Simple worker queue that limits concurrent job execution."""

    def __init__(self, max_workers: int) -> None:
        self._queue: "Queue[Callable[[], None]]" = Queue()
        self._threads: list[threading.Thread] = []
        self._shutdown = threading.Event()
        for _ in range(max_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._threads.append(t)

    def _worker(self) -> None:
        while not self._shutdown.is_set():
            func = self._queue.get()
            try:
                func()
            finally:
                self._queue.task_done()

    def enqueue(self, func: Callable[[], None]) -> None:
        """Add a callable to be executed by the worker pool."""
        self._queue.put(func)

    def join(self) -> None:
        self._queue.join()

    def shutdown(self) -> None:
        self._shutdown.set()
        for _ in self._threads:
            self.enqueue(lambda: None)
        for t in self._threads:
            t.join()


class BrokerJobQueue(JobQueue):
    """Placeholder for external job broker integration."""

    def enqueue(self, func: Callable[[], None]) -> None:  # pragma: no cover - stub
        raise NotImplementedError("Broker based queue not implemented")

    def shutdown(self) -> None:  # pragma: no cover - stub
        pass
