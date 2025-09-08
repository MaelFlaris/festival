from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0004_rename_tickets_typ_edition_phase_active_idx_tickets_tic_edition_4bf338_idx_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="tickettype",
            options={
                "ordering": ["code"],
                "unique_together": [("edition", "code")],
                "permissions": [("manage_pricing", "Peut gérer phases/prix")],
            },
        ),
    ]

