from django.db import migrations, models

def copy_existing_accessory(apps, schema_editor):
    Outfit = apps.get_model("mixmatch", "Outfit")
    through = Outfit.accessories.through

    for outfit in Outfit.objects.exclude(
        accessories_legacy__isnull=True
    ).iterator():
        through.objects.get_or_create(
            outfit_id=outfit.pk,
            item_id=outfit.accessories_legacy_id,
        )

class Migration(migrations.Migration):
    dependencies = [
        ("mixmatch", "0002_outfit_dresses_outfit_outerwear"),
        (
            "closet",
            "0006_item_date_purchased_item_price_item_purchase_link_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="outfit",
            old_name="accessories",
            new_name="accessories_legacy",
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="outfit",
                    name="accessories",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="outfits_with_accessory",
                        to="closet.item",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            copy_existing_accessory,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="outfit",
            name="accessories_legacy",
        ),
    ]