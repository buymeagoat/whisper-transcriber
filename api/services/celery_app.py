from __future__ import annotations

from celery import Celery

from api.settings import settings
from api.config_validator import validate_config

validate_config()

celery_app = Celery(
    "whisper_transcriber",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
)

# Avoid Celery printing duplicate banners when the worker starts or
# stops by disabling the root logger hijack and stdout redirection.
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
)


@celery_app.task(name="run_callable")
def run_callable(pickled_func: bytes) -> None:
    import pickle

    func = pickle.loads(pickled_func)
    func()
