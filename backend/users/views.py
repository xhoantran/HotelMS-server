from django.contrib.sites.models import Site
from django.shortcuts import redirect
from rest_framework import generics, permissions


class AccountConfirmEmailRedirectView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def redirect(self, request, *args, **kwargs):
        site = Site.objects.get_current()
        return redirect(
            f"https://{site.domain}/auth/account-confirm-email/?key={kwargs['key']}"
        )

    def get(self, request, *args, **kwargs):
        return self.redirect(request, *args, **kwargs)


class PasswordResetConfirmRedirectView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def redirect(self, request, *args, **kwargs):
        site = Site.objects.get_current()
        return redirect(
            f"https://{site.domain}/auth/password-reset-confirm/?uid={kwargs['uid']}&token={kwargs['token']}"
        )

    def get(self, request, *args, **kwargs):
        return self.redirect(request, *args, **kwargs)
