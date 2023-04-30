from django.apps import apps
from django.contrib import admin

from .models import User

for model in apps.get_models():
    if model.__name__ and admin.site.is_registered(model):
        admin.site.unregister(model)


admin.site.register(User)
