from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import planner.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("mixmatch", "0002_outfit_dresses_outfit_outerwear")]
    operations = [
        migrations.CreateModel(
            name="PlannerSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("laundry_weekdays", models.JSONField(blank=True, default=planner.models.default_laundry_weekdays)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="planner_settings", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="DailyPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("outfit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="daily_plans", to="mixmatch.outfit")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="daily_outfit_plans", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["date"]},
        ),
        migrations.AddConstraint(model_name="dailyplan", constraint=models.UniqueConstraint(fields=("user", "date"), name="planner_unique_user_date")),
    ]
