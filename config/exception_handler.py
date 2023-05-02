from django.core import exceptions
from django.views import View
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import exception_handler
from rest_framework.settings import api_settings


def custom_exception_handler(exc: Exception, context: View):
    response = exception_handler(exc, context)

    if isinstance(exc, exceptions.ValidationError):
        if hasattr(exc, "message_dict"):
            data = exc.message_dict
        elif hasattr(exc, "message"):
            data = {api_settings.NON_FIELD_ERRORS_KEY: exc.message}

        return DRFResponse(
            data=data,
            status=HTTP_400_BAD_REQUEST,
        )

    return response
