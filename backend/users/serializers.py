from dj_rest_auth.serializers import (
    UserDetailsSerializer as DJRestAuthUserDetailsSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserDetailSerializer(DJRestAuthUserDetailsSerializer):
    class Meta:
        model = User
        fields = ("pk", "username", "email", "name")
        read_only_fields = ("email",)
