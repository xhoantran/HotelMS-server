"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="YmyhFpakqspmMDrrQbyRbyUjifiFTMcEdSfgtrwqGtCrouoPm5EeuTFk9Atwj7RB",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore # noqa F405

# BENCHMARKING
# ------------------------------------------------------------------------------
INSTALLED_APPS += ["nplusone.ext.django"]  # noqa F405

MIDDLEWARE += ["nplusone.ext.django.NPlusOneMiddleware"]  # noqa F405


# Channex
# ------------------------------------------------------------------------------
CHANNEX_API_KEY = "udyfXJJqaCvV+3Nkti7FMejZ6GKSP/1wOUbDDFp/pRNisbBXjHhtuN3O3opTFlqK"
CHANNEX_BASE_URL = "https://staging.channex.io/api/v1/"
CHANNEX_PROPERTY_ID = "ced3f420-fba8-41cf-9a1e-61c4896da83a"
