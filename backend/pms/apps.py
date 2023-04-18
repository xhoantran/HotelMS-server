from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PmsConfig(AppConfig):
    name = "backend.pms"
    verbose_name = _("PMS")

    def ready(self):
        import backend.pms.signals  # noqa F401
