from __future__ import annotations

from celery import Celery

from api.settings import settings

celery_app = Celery(
    "whisper_transcriber",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
)


@celery_app.task(name="run_callable")
def run_callable(pickled_func: bytes) -> None:
    import pickle

    func = pickle.loads(pickled_func)
    func()
