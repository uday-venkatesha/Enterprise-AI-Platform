from celery import Celery

from app.config import settings

# The Celery application object. "enterprise_ai" is just a name. broker= is
# where jobs are queued (Redis); backend= is where results are stored.
celery_app = Celery(
    "enterprise_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Tell Celery which module(s) contain task definitions, so it registers them
# when the worker starts. We'll put our tasks in app.worker.tasks (next).
celery_app.autodiscover_tasks(["app.worker"])