from rest_framework import status
from rest_framework.test import APIRequestFactory

from ..views import AccountConfirmEmailRedirectView, PasswordResetConfirmRedirectView


def test_account_confirm_email_redirect_view(current_site):
    factory = APIRequestFactory()
    request = factory.get("/fake-url/")
    view = AccountConfirmEmailRedirectView.as_view()

    response = view(request, key="testkey")
    assert response.status_code == status.HTTP_302_FOUND
    assert (
        response.url
        == f"https://{current_site.domain}/auth/account-confirm-email/?key=testkey"
    )


def test_password_reset_confirm_redirect_view(current_site):
    factory = APIRequestFactory()
    request = factory.get("/fake-url/")
    view = PasswordResetConfirmRedirectView.as_view()

    response = view(request, uid="testuid", token="testtoken")
    assert response.status_code == status.HTTP_302_FOUND
    assert (
        response.url
        == f"https://{current_site.domain}/auth/password-reset-confirm/?uid=testuid&token=testtoken"
    )
