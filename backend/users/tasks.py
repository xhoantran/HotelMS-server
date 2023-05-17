from anymail.exceptions import AnymailAPIError

from backend.users.mail import render_mail
from config.celery_app import app


@app.task(retries=3, autoretry_for=(AnymailAPIError,), retry_backoff=60)
def send_email(template_prefix, recipients, context, headers=None):
    msg = render_mail(template_prefix, recipients, context, headers)
    msg.send()
