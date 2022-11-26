from datetime import timedelta
import logging

from celery.decorators import periodic_task
from django.conf import settings
from django.utils import timezone

from vision_backend.tasks import (
    check_source, classify_image, deploy, submit_classifier, submit_features)
from .models import Job
from .utils import full_job

logger = logging.getLogger(__name__)


# Each Job is assumed to start with a Celery task. It doesn't necessarily
# have to finish at the end of that same task.
# For lack of more clever solutions, we'll map from job names to
# starter tasks here.
job_starter_tasks = {
    'check_source': check_source,
    'classify_features': classify_image,
    'classify_image': deploy,
    'train_classifier': submit_classifier,
    'extract_features': submit_features,
}


def get_scheduled_jobs():
    jobs = Job.objects.filter(status=Job.PENDING)
    # We're repurposing this celery setting to determine whether to run
    # pending jobs immediately. (It's similar to celery's semantics for
    # this setting.)
    if not settings.CELERY_ALWAYS_EAGER:
        jobs = jobs.filter(scheduled_start_time__lt=timezone.now())
    return jobs


@periodic_task(
    run_every=timedelta(minutes=5),
    ignore_result=True,
)
@full_job()
def run_scheduled_jobs():
    for job in get_scheduled_jobs():
        starter_task = job_starter_tasks[job.job_name]
        starter_task.delay(*Job.identifier_to_args(job.arg_identifier))


def run_scheduled_jobs_until_empty():
    """
    For testing purposes, it's convenient to schedule + run jobs, and
    then also run the jobs which have been scheduled by those jobs,
    using just one call.
    """
    while get_scheduled_jobs().exists():
        run_scheduled_jobs()


@periodic_task(
    run_every=timedelta(days=1),
    ignore_result=True)
def clean_up_old_jobs():
    current_time = timezone.now()
    thirty_days_ago = current_time - timedelta(days=30)

    old_jobs = Job.objects.filter(scheduled_start_time__lt=thirty_days_ago)
    old_jobs.delete()
