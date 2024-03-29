from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from backend.pms.models import HotelEmployee, RatePlan, RatePlanRestrictions, Room

User = get_user_model()


@receiver(post_save, sender=User, dispatch_uid="pms:post_save_user")
def post_save_user(sender, instance, created, **kwargs):
    if created:
        if instance.role in (
            User.UserRoleChoices.MANAGER,
            User.UserRoleChoices.RECEPTIONIST,
            User.UserRoleChoices.STAFF,
        ):
            HotelEmployee.objects.create(user=instance)
            # is_active is set to False by default, and we want to set it to True
            # when a hotel is assigned to the user
            instance.is_active = False
            instance.save(update_fields=["is_active"])


@receiver(post_save, sender=HotelEmployee, dispatch_uid="pms:post_save_hotel_employee")
def post_save_hotel_employee(sender, instance: HotelEmployee, created, **kwargs):
    if instance.hotel and instance.user.is_active is False:
        instance.user.is_active = True
        instance.user.save(update_fields=["is_active"])


@receiver(post_save, sender=RatePlan, dispatch_uid="pms:post_save_rate_plan")
def post_save_rate_plan(sender, instance: RatePlan, created, **kwargs):
    if created:
        rate_plan_restrictions = []
        window = instance.room_type.hotel.inventory_days
        for i in range(window + 1):
            rate_plan_restrictions.append(
                RatePlanRestrictions(
                    rate_plan=instance,
                    date=timezone.now() + timezone.timedelta(days=i),
                    rate=0,
                )
            )
        RatePlanRestrictions.objects.bulk_create(rate_plan_restrictions)


@receiver(pre_save, sender=Room, dispatch_uid="pms:validate_room")
def validate_room(sender, instance: Room, **kwargs):
    if instance.number < 0:
        raise ValidationError("Room number must be positive")
    if Room.objects.filter(
        Q(
            room_type__hotel=instance.room_type.hotel,
            number=instance.number,
        )
        & ~Q(id=instance.id)
    ).exists():
        raise ValidationError("Room number must be unique for the hotel")
