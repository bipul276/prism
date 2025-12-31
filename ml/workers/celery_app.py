from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis URL from docker-compose or env
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "prism_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["ml.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
)
