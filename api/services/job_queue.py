from __future__ import annotations

import threading
from queue import Queue
from typing import Callable
import time

from prometheus_client import Counter, Gauge, Histogram

# Prometheus metrics
jobs_queued_total = Counter("jobs_queued_total", "Total jobs queued")
jobs_in_progress = Gauge("jobs_in_progress", "Jobs currently executing")
job_duration_seconds = Histogram(
    "job_duration_seconds", "Time spent executing job in seconds"
)
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
        self._queue: "Queue[Callable[[], None] | None]" = Queue()
        self._threads: list[threading.Thread] = []
        self._shutdown = threading.Event()
        self._lock = threading.Lock()
        for _ in range(max_workers):
            self._start_thread()

    def _start_thread(self) -> None:
        t = threading.Thread(target=self._worker, daemon=True)
        t.start()
        self._threads.append(t)

    def _worker(self) -> None:
        while True:
            func = self._queue.get()
            if func is None:
                self._queue.task_done()
                break
            try:
                jobs_in_progress.inc()
                start = time.perf_counter()
                func()
            finally:
                duration = time.perf_counter() - start
                job_duration_seconds.observe(duration)
                jobs_in_progress.dec()
                self._queue.task_done()
        with self._lock:
            if threading.current_thread() in self._threads:
                self._threads.remove(threading.current_thread())

    def enqueue(self, func: Callable[[], None]) -> None:
        """Add a callable to be executed by the worker pool."""
        jobs_queued_total.inc()
        self._queue.put(func)

    def join(self) -> None:
        self._queue.join()

    def shutdown(self) -> None:
        self._shutdown.set()
        with self._lock:
            for _ in self._threads:
                self._queue.put(None)
            threads = list(self._threads)
        for t in threads:
            t.join()
        with self._lock:
            self._threads.clear()

    def resize(self, max_workers: int) -> None:
        with self._lock:
            current = len(self._threads)
            if max_workers > current:
                for _ in range(max_workers - current):
                    self._start_thread()
            elif max_workers < current:
                for _ in range(current - max_workers):
                    self._queue.put(None)


class BrokerJobQueue(JobQueue):
    """Queue jobs by delegating execution to a Celery worker."""

    def __init__(self) -> None:
        from .celery_app import celery_app, run_callable

        self._celery_app = celery_app
        self._task_name = run_callable.name

    def enqueue(self, func: Callable[[], None]) -> None:
        """Serialize the callable and submit it to Celery."""
        import pickle

        payload = pickle.dumps(func)
        self._celery_app.send_task(self._task_name, args=(payload,))

    def shutdown(self) -> None:
        """Close Celery connections if possible."""
        close = getattr(self._celery_app, "close", None)
        if callable(close):
            close()
