import uuid

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, TextChoices, UUIDField
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for HotelMS.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    #: First and last name do not cover name patterns around the globe
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    class UserRoleChoices(TextChoices):
        ADMIN = "admin", _("Admin")
        MANAGER = "manager", _("Manager")
        STAFF = "staff", _("Staff")
        RECEPTIONIST = "receptionist", _("Receptionist")
        GUEST = "guest", _("Guest")

    role = CharField(
        _("Role"),
        max_length=16,
        choices=UserRoleChoices.choices,
        default=UserRoleChoices.GUEST,
    )
