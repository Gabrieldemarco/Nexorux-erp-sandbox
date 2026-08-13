from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "nexorux-erp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Montevideo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

if settings.DEBUG:
    celery_app.conf.task_always_eager = True
    celery_app.conf.result_backend = "cache+memory://"
