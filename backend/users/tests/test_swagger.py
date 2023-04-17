from django.urls import reverse


def test_swagger_accessible_by_super_admin(super_admin, get_api_client):
    url = reverse("api-docs")
    super_admin_api_client = get_api_client(super_admin)
    response = super_admin_api_client.get(url)
    assert response.status_code == 200


def test_swagger_ui_not_accessible_by_normal_user(user, get_api_client):
    url = reverse("api-docs")
    api_client = get_api_client(user)
    response = api_client.get(url)
    assert response.status_code == 403


def test_api_schema_generated_successfully(super_admin, get_api_client):
    url = reverse("api-schema")
    super_admin_api_client = get_api_client(super_admin)
    response = super_admin_api_client.get(url)
    assert response.status_code == 200
