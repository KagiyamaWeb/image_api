from celery import Celery
import os

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery.conf.update(
    task_routes={
        'app.tasks.process_image': {'queue': 'images'},
    },
)