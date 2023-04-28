from django.conf import settings
from django.shortcuts import redirect
from rest_framework import generics, permissions

FRONTEND_BASE_URL = settings.FRONTEND_BASE_URL


class AccountConfirmEmailRedirectView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def redirect(self, request, *args, **kwargs):
        return redirect(f"{FRONTEND_BASE_URL}/auth/email-confirm/?key={kwargs['key']}")

    def get(self, request, *args, **kwargs):
        return self.redirect(request, *args, **kwargs)


class PasswordResetConfirmRedirectView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def redirect(self, request, *args, **kwargs):
        return redirect(
            f"{FRONTEND_BASE_URL}/auth/password-reset-confirm/?uid={kwargs['uid']}&token={kwargs['token']}"
        )

    def get(self, request, *args, **kwargs):
        return self.redirect(request, *args, **kwargs)
