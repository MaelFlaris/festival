# Generated manually for V2 fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_alter_tickettype_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='tickettype',
            name='phase',
            field=models.CharField(choices=[('early','Early'),('regular','Regular'),('late','Late')], default='regular', max_length=10, db_index=True),
        ),
        migrations.AddField(
            model_name='tickettype',
            name='quota_by_channel',
            field=models.JSONField(blank=True, default=dict, help_text='{"online": 0, "partner": 0} (≤ quota_total)'),
        ),
        migrations.AddField(
            model_name='tickettype',
            name='reserved_by_channel',
            field=models.JSONField(blank=True, default=dict, help_text='{"online": 0, "partner": 0} (≤ quota_by_channel)'),
        ),
        migrations.AddIndex(
            model_name='tickettype',
            index=models.Index(fields=['edition','phase','is_active'], name='tickets_typ_edition_phase_active_idx'),
        ),
        migrations.AddIndex(
            model_name='tickettype',
            index=models.Index(fields=['edition','day','is_active'], name='tickets_typ_edition_day_active_idx'),
        ),
    ]
