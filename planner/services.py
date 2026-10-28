from datetime import timedelta

from closet.models import Item
from mixmatch.models import SLOTS

from .models import DailyPlan, PlannerSettings


def next_laundry_day(start_date, weekdays):
    """Return the first configured laundry date on or after start_date."""
    candidates = [
        start_date + timedelta(days=offset)
        for offset in range(7)
        if (start_date + timedelta(days=offset)).weekday() in weekdays
    ]
    return min(candidates) if candidates else None


def ready_date_for_slot(slot_date, weekdays, laundry_time_days):
    """A planned wear starts washing the next day and resets after laundry."""
    laundry_date = next_laundry_day(slot_date + timedelta(days=1), weekdays)
    return laundry_date + timedelta(days=laundry_time_days) if laundry_date else None


def washing_item_ids(user, target_date, weekdays, laundry_time_days, exclude_plan=None):
    """Compute Planner wash state using plans and dates, never Item.status."""
    if not weekdays:
        return set()
    earliest_slot = target_date - timedelta(days=laundry_time_days + 8)
    plans = DailyPlan.objects.filter(
        user=user, date__gte=earliest_slot, date__lt=target_date
    ).select_related("outfit")
    if exclude_plan is not None:
        plans = plans.exclude(pk=exclude_plan.pk)

    washing = set()
    for plan in plans:
        ready_date = ready_date_for_slot(plan.date, weekdays, laundry_time_days)
        if plan.date < target_date < ready_date:
            washing.update(
                item_id
                for slot in SLOTS
                if (item_id := getattr(plan.outfit, f"{slot}_id")) is not None
            )
    return washing


def sync_item_statuses(user, on_date=None):
    """Mirror today's Planner-derived state into Closet Item.status."""
    from django.utils import timezone

    today = on_date or timezone.localdate()
    settings, _ = PlannerSettings.objects.get_or_create(user=user)
    washing_ids = washing_item_ids(
        user, today, settings.laundry_weekdays, settings.laundry_time_days
    )
    items = list(Item.objects.filter(user=user))
    changed = []
    for item in items:
        status = "washing" if item.pk in washing_ids else "ready"
        if item.status != status:
            item.status = status
            changed.append(item)
    if changed:
        Item.objects.bulk_update(changed, ["status"])
