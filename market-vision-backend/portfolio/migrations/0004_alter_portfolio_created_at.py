# Generated manually to align model state

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0003_trade_refactor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="portfolio",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
