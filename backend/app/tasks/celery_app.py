from celery import Celery
from celery.signals import setup_logging

from app.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "fairlens",
    broker=_settings.CELERY_BROKER_URL,
    backend=_settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.audit_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=600,        # 10 min hard limit
    task_soft_time_limit=540,   # 9 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=86400,       # 1 day
)


@setup_logging.connect
def _config_logging(*_args, **_kwargs):
    import logging
    logging.basicConfig(level=_settings.LOG_LEVEL)
