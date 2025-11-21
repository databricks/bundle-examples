from dataclasses import replace


from databricks.bundles.core import Bundle, job_mutator, m
from databricks.bundles.jobs import Job, JobEmailNotifications


@job_mutator
def add_email_notifications(bundle: Bundle, job: Job) -> Job:
    if job.email_notifications:
        return job


    email_notifications = JobEmailNotifications.from_dict(
        {
            "on_failure": ["${workspace.current_user.userName}"],
        }
    )


    return replace(job, email_notifications=email_notifications)
