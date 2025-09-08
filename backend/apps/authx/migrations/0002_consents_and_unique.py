from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authx", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="consents",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddConstraint(
            model_name="userprofile",
            constraint=models.UniqueConstraint(fields=("user",), name="uniq_authx_profile_user"),
        ),
    ]
