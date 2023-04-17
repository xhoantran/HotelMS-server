from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.role == request.user.UserRoleChoices.ADMIN
        except AttributeError:
            return False


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return (
                request.user.role == request.user.UserRoleChoices.MANAGER
                and request.user.is_active
            )
        except AttributeError:
            return False


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return (
                request.user.role == request.user.UserRoleChoices.STAFF
                and request.user.is_active
            )
        except AttributeError:
            return False


class IsReceptionist(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return (
                request.user.role == request.user.UserRoleChoices.RECEPTIONIST
                and request.user.is_active
            )
        except AttributeError:
            return False


class IsGuest(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.role == request.user.UserRoleChoices.GUEST
        except AttributeError:
            return False


class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.role in [
                request.user.UserRoleChoices.MANAGER,
                request.user.UserRoleChoices.STAFF,
                request.user.UserRoleChoices.RECEPTIONIST,
            ]
        except AttributeError:
            return False


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
