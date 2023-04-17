from django.urls import include, path

from .views import AccountConfirmEmailRedirectView, PasswordResetConfirmRedirectView

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path(
        "registration/account-confirm-email/<str:key>/",
        AccountConfirmEmailRedirectView.as_view(),
        name="account_confirm_email",
    ),
    path(
        "registration/password-reset-confirm/<str:uid>/<str:token>/",
        PasswordResetConfirmRedirectView.as_view(),
        name="password_reset_confirm",
    ),
    path("registration/", include("dj_rest_auth.registration.urls")),
]
