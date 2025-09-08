from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sponsors", "0003_sponsorship_sponsors_sp_edition_039656_idx"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sponsorship",
            options={
                "ordering": ["tier__rank", "order", "sponsor__name"],
                "unique_together": [("edition", "sponsor")],
                "permissions": [("view_financials", "Peut voir les montants confidentiels")],
            },
        ),
    ]
