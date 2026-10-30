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

def ensure_accessories_table(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "mixmatch_outfit_accessories" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "outfit_id" bigint NOT NULL
                    REFERENCES "mixmatch_outfit" ("id")
                    DEFERRABLE INITIALLY DEFERRED,
                "item_id" bigint NOT NULL
                    REFERENCES "closet_item" ("id")
                    DEFERRABLE INITIALLY DEFERRED
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            "mixmatch_outfit_accessories_outfit_id_item_id_00b4c96a_uniq"
            ON "mixmatch_outfit_accessories" ("outfit_id", "item_id")
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            "mixmatch_outfit_accessories_outfit_id_4fa51df9"
            ON "mixmatch_outfit_accessories" ("outfit_id")
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            "mixmatch_outfit_accessories_item_id_737e76ae"
            ON "mixmatch_outfit_accessories" ("item_id")
        """)

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
            database_operations=[
                migrations.RunPython(
                    ensure_accessories_table,
                    migrations.RunPython.noop,
                ),
            ],
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