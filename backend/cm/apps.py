from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CmConfig(AppConfig):
    name = "backend.cm"
    verbose_name = _("Channel Manager Connector")

    def ready(self):
        import backend.cm.signals  # noqa F401
