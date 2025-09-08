from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("schedule", "0002_alter_slot_setlist_urls"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="slot",
            options={
                "ordering": ["day", "stage__name", "start_time"],
                "permissions": [("manage_slot", "Peut gérer le slot (annuler/confirmer)")],
            },
        ),
    ]

