from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0003_alter_news_status_alter_page_status"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="page",
            options={
                "ordering": ["slug"],
                "unique_together": [("edition", "slug")],
                "permissions": [("publish_page", "Peut publier la page")],
            },
        ),
        migrations.AlterModelOptions(
            name="news",
            options={
                "ordering": ["-publish_at", "-created_at"],
                "permissions": [("publish_news", "Peut publier l'actualité")],
            },
        ),
    ]

