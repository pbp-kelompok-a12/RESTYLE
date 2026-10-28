from django.conf import settings
from django.db import models
from mixmatch.models import Outfit

def default_laundry_weekdays():
    return [6]


class PlannerSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="planner_settings")
    # ISO weekdays: Monday=0 through Sunday=6.
    laundry_weekdays = models.JSONField(default=default_laundry_weekdays, blank=True)


class DailyPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_outfit_plans")
    date = models.DateField()
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, related_name="daily_plans")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "date"), name="planner_unique_user_date")]
        ordering = ["date"]
