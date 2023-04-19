from decimal import Decimal

import pytest
from django.utils import timezone

from ..models import LeadDaysBasedRule


# def test_dynamic_pricing_adapter_cache(
#     dynamic_pricing_adapter,
#     hotel_factory,
#     room_type_factory,
#     django_assert_num_queries,
# ):
#     hotel = hotel_factory()
#     room_type_factory.create_batch(10, hotel=hotel)
#     hotel_id = str(hotel.id)
#     adapter = dynamic_pricing_adapter(hotel=hotel)
#     db_weekday_based_rules = adapter.weekday_based_rules
#     db_month_based_rules = adapter.month_based_rules
#     db_season_based_rules = adapter.season_based_rules
#     db_availability_based_trigger_rules = adapter.availability_based_trigger_rules
#     db_lead_days_based_rules = adapter.lead_days_based_rules
#     with django_assert_num_queries(1):
#         adapter = dynamic_pricing_adapter(hotel=hotel_id)
#         assert adapter.weekday_based_rules == db_weekday_based_rules
#         assert adapter.month_based_rules == db_month_based_rules
#         assert adapter.season_based_rules == db_season_based_rules
#         assert (
#             adapter.availability_based_trigger_rules
#             == db_availability_based_trigger_rules
#         )
#         assert adapter.lead_days_based_rules == db_lead_days_based_rules


# def test_dynamic_pricing_adapter_default(
#     dynamic_pricing_adapter,
#     dynamic_pricing_setting_factory,
#     room_type_factory,
#     hotel_factory,
#     property_factory,
# ):
#     with pytest.raises(ValueError):
#         dynamic_pricing_adapter(hotel=None)
#     hotel = hotel_factory()
#     adapter = dynamic_pricing_adapter(hotel=hotel.id)  # uuid
#     room_type = room_type_factory(hotel=hotel)
#     assert (
#         adapter.get_room_type_availability_based_factor(
#             room_type=room_type,
#             date=timezone.now().date(),
#         )
#         == 1
#     )
#     assert adapter.get_lead_days_based_factor(date=timezone.now().date()) == 1
#     assert adapter.is_enabled
#     assert adapter.is_lead_days_based
#     assert adapter.is_weekday_based
#     assert adapter.is_month_based
#     assert adapter.is_season_based
#     assert adapter.is_availability_based

#     cm_property = property_factory()
#     dynamic_pricing = dynamic_pricing_setting_factory(cm_property=cm_property)
#     adapter = dynamic_pricing_adapter(cm_property=cm_property)
#     assert adapter.setting.id == dynamic_pricing.id


# def test_dynamic_pricing_adapter_availability_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     availability_based_rule_factory,
#     booking_factory,
# ):
#     room1 = room_factory()
#     rules = availability_based_rule_factory.create_batch(
#         2, setting=room1.room_type.hotel.dynamic_pricing_setting
#     )
#     adapter = dynamic_pricing_adapter(hotel=room1.room_type.hotel)
#     booking_factory(room=room1, start_date=timezone.now().date())
#     assert pytest.approx(
#         adapter.get_room_type_availability_based_factor(
#             room_type=room1.room_type, date=timezone.now().date()
#         )
#     ) == Decimal(rules[0].multiplier_factor)

#     room2 = room_factory(room_type=room1.room_type)
#     booking_factory(room=room2, start_date=timezone.now().date())
#     assert pytest.approx(
#         adapter.get_room_type_availability_based_factor(
#             room_type=room2.room_type, date=timezone.now().date()
#         )
#     ) == Decimal(rules[1].multiplier_factor)


# def test_dynamic_pricing_adapter_lead_days_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     booking_factory,
# ):
#     room = room_factory()
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     booking_factory(room=room, start_date=timezone.now().date())
#     last_rule = (
#         LeadDaysBasedRule.objects.filter(
#             setting=room.room_type.hotel.dynamic_pricing_setting
#         )
#         .order_by("-lead_days")
#         .first()
#     )
#     inventory_days = room.room_type.hotel.inventory_days
#     assert pytest.approx(
#         adapter.get_lead_days_based_factor(
#             date=timezone.now().date() + timezone.timedelta(days=inventory_days + 1)
#         )
#     ) == Decimal(last_rule.multiplier_factor)

#     with pytest.raises(ValueError):
#         adapter.get_lead_days_based_factor(
#             date=timezone.now().date() - timezone.timedelta(days=1)
#         )


# def test_dynamic_pricing_adapter_calculate_room_type_rate(
#     dynamic_pricing_adapter, room_factory, booking_factory
# ):
#     room = room_factory()
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     booking_factory(room=room, start_date=timezone.now().date())
#     assert room.room_type.base_rate == adapter.get_room_type_base_rate(
#         room_type=room.room_type
#     )


# def test_dynamic_pricing_adapter_calculate_room_type_rate_with_lead_days_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     lead_days_based_rule_factory,
#     booking_factory,
# ):
#     room = room_factory()
#     lead_days_based_rule_factory(
#         setting=room.room_type.hotel.dynamic_pricing_setting,
#         lead_days=0,
#         multiplier_factor=0.5,
#     )
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     booking_factory(room=room, start_date=timezone.now().date())
#     assert room.room_type.base_rate / 2 == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )

#     adapter.setting.is_lead_days_based = False
#     adapter.setting.save()
#     adapter.invalidate_cache()
#     adapter.load_from_db()
#     assert room.room_type.base_rate == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )


# def test_dynamic_pricing_adapter_calculate_room_type_rate_with_weekday_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     weekday_based_rule_factory,
# ):
#     room = room_factory()
#     weekday_based_rule = weekday_based_rule_factory(
#         setting=room.room_type.hotel.dynamic_pricing_setting,
#         weekday=timezone.now().date().weekday(),
#     )
#     weekday_based_rule.multiplier_factor = 2
#     weekday_based_rule.save()
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     assert adapter.get_weekday_based_factor(date=timezone.now().date()) == 2
#     assert room.room_type.base_rate * 2 == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )

#     adapter.setting.is_weekday_based = False
#     adapter.setting.save()
#     adapter.invalidate_cache()
#     adapter.load_from_db()
#     assert room.room_type.base_rate == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )


# def test_dynamic_pricing_adapter_calculate_room_type_rate_with_month_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     month_based_rule_factory,
# ):
#     room = room_factory()
#     month_based_rule = month_based_rule_factory(
#         setting=room.room_type.hotel.dynamic_pricing_setting,
#         month=timezone.now().date().month,
#     )
#     month_based_rule.multiplier_factor = 2
#     month_based_rule.save()
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     assert adapter.get_month_based_factor(date=timezone.now().date()) == 2
#     assert room.room_type.base_rate * 2 == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )

#     adapter.setting.is_month_based = False
#     adapter.setting.save()
#     adapter.invalidate_cache()
#     adapter.load_from_db()
#     assert room.room_type.base_rate == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )


# def test_dynamic_pricing_adapter_calcuclate_room_type_with_season_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     season_based_rule_factory,
# ):
#     room = room_factory()
#     season_based_rule = season_based_rule_factory(
#         setting=room.room_type.hotel.dynamic_pricing_setting,
#         start_date=timezone.now().date(),
#         end_date=timezone.now().date() + timezone.timedelta(days=10),
#     )
#     season_based_rule.multiplier_factor = 2
#     season_based_rule.save()
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     assert (
#         adapter.get_season_based_factor(
#             date=timezone.now().date() + timezone.timedelta(days=5)
#         )
#         == 2
#     )
#     assert room.room_type.base_rate * 2 == adapter.calculate_rate(
#         room_type=room.room_type,
#         date=timezone.now().date() + timezone.timedelta(days=5),
#     )

#     adapter.setting.is_season_based = False
#     adapter.setting.save()
#     adapter.invalidate_cache()
#     adapter.load_from_db()
#     assert room.room_type.base_rate == adapter.calculate_rate(
#         room_type=room.room_type,
#         date=timezone.now().date() + timezone.timedelta(days=5),
#     )


# def test_dynamic_pricing_adapter_calculate_room_type_rate_with_availability_based(
#     dynamic_pricing_adapter,
#     room_factory,
#     availability_based_rule_factory,
#     booking_factory,
# ):
#     room = room_factory()
#     availability_based_rule_factory(
#         setting=room.room_type.hotel.dynamic_pricing_setting,
#         max_availability=1,
#         multiplier_factor=0.5,
#     )
#     adapter = dynamic_pricing_adapter(hotel=room.room_type.hotel)
#     booking_factory(room=room, start_date=timezone.now().date())
#     assert room.room_type.base_rate / 2 == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )

#     adapter.setting.is_availability_based = False
#     adapter.setting.save()
#     adapter.invalidate_cache()
#     adapter.load_from_db()

#     assert room.room_type.base_rate == adapter.calculate_rate(
#         room_type=room.room_type, date=timezone.now().date()
#     )
