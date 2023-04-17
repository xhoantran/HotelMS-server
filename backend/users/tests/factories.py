from collections.abc import Sequence
from typing import Any

from django.contrib.auth import get_user_model
from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from backend.pms.tests.factories import HotelEmployeeFactory


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @post_generation
    def role(self, create: bool, extracted: Sequence[Any], **kwargs):
        if not create:
            return

        if extracted:
            self.role = extracted

        if extracted in [
            get_user_model().UserRoleChoices.MANAGER,
            get_user_model().UserRoleChoices.STAFF,
            get_user_model().UserRoleChoices.RECEPTIONIST,
        ]:
            self.hotel_employee = HotelEmployeeFactory(user=self)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


class SuperAdminFactory(UserFactory):
    is_staff = True
    is_superuser = True

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


class CurrentSiteFactory(DjangoModelFactory):
    domain = Faker("domain_name")
    name = Faker("name")

    class Meta:
        model = "sites.Site"
        django_get_or_create = ["domain"]
