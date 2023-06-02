import pgtrigger

from backend.pms.models import RatePlan, RatePlanRestrictions

from .models import RMSRatePlan, RMSRatePlanRestrictions

"""
We want loosely coupled code, so we separate the data domain of the PMS. But
we still want to keep the data integrity. So we use triggers to create the
associated data in the RMS domain when the data in the PMS domain is created.
"""
pgtrigger.register(
    pgtrigger.Trigger(
        name="rms_rateplan_restrictions_insert",
        operation=pgtrigger.Insert,
        when=pgtrigger.After,
        func=f"""
          INSERT INTO {RMSRatePlanRestrictions._meta.db_table} (restriction_id, base_rate)
          VALUES (NEW.id, 0);
          RETURN NEW;
        """,
    ),
)(RatePlanRestrictions)

pgtrigger.register(
    pgtrigger.Trigger(
        name="rms_rateplan_insert",
        operation=pgtrigger.Insert,
        when=pgtrigger.After,
        func=f"""
          INSERT INTO {RMSRatePlan._meta.db_table} (rate_plan_id, percentage_factor, increment_factor, updated_at)
          VALUES (NEW.id, 0, 0, NOW());
          RETURN NEW;
        """,
    ),
)(RatePlan)
