# Generated manually for portfolio refactor

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fixings", "0002_market_rework"),
        ("portfolio", "0002_remove_indexpacket_initialprice"),
    ]

    operations = [
        migrations.AddField(
            model_name="portfolio",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="Trade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("side", models.CharField(choices=[("BUY", "Buy"), ("SELL", "Sell")], default="BUY", max_length=4)),
                ("quantity", models.DecimalField(decimal_places=6, max_digits=20, verbose_name="Количество")),
                ("price_per_share", models.DecimalField(decimal_places=6, max_digits=20, verbose_name="Цена за акцию")),
                ("tradeDate", models.DateField(verbose_name="Дата сделки")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "portfolioId",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trades", to="portfolio.portfolio"),
                ),
                ("stockId", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="fixings.index", verbose_name="Акция")),
            ],
            options={
                "verbose_name": "Сделка",
                "verbose_name_plural": "Сделки",
                "ordering": ["-tradeDate", "-id"],
            },
        ),
        migrations.DeleteModel(
            name="IndexPacket",
        ),
    ]
