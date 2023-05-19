from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string


def render_mail(template_prefix, email, context, headers=None):
    """
    Renders an e-mail to `email`.  `template_prefix` identifies the
    e-mail that is to be sent, e.g. "email/setup_hotel_confirmation"
    """
    to = [email] if isinstance(email, str) else email
    subject = render_to_string(f"{template_prefix}_subject.txt", context)
    # remove superfluous line breaks
    subject = " ".join(subject.splitlines()).strip()

    from_email = settings.DEFAULT_FROM_EMAIL

    bodies = {}
    for ext in ["html", "txt"]:
        try:
            template_name = f"{template_prefix}_message.{ext}"
            bodies[ext] = render_to_string(
                template_name,
                context,
            ).strip()
        except TemplateDoesNotExist:
            if ext == "txt" and not bodies:
                # We need at least one body
                raise
    if "txt" in bodies:
        msg = EmailMultiAlternatives(
            subject, bodies["txt"], from_email, to, headers=headers
        )
        if "html" in bodies:
            msg.attach_alternative(bodies["html"], "text/html")
    else:
        msg = EmailMessage(subject, bodies["html"], from_email, to, headers=headers)
        msg.content_subtype = "html"  # Main content is now text/html
    return msg
