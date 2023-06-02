from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RmsConfig(AppConfig):
    name = "backend.rms"
    verbose_name = _("Revenue Management System")

    def ready(self):
        import backend.rms.pg_triggers  # noqa F401
        import backend.rms.signals  # noqa F401
