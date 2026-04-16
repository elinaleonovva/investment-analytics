# Generated manually to align model state

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fixings", "0002_market_rework"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="currencyusdfixing",
            options={"constraints": [], "verbose_name": "Фиксинг валюты", "verbose_name_plural": "Фиксинги валют"},
        ),
        migrations.AlterModelOptions(
            name="fixing",
            options={"constraints": [], "verbose_name": "Фиксинг акции", "verbose_name_plural": "Фиксинги акций"},
        ),
        migrations.AlterField(
            model_name="currency",
            name="symbol",
            field=models.CharField(blank=True, default="RUB", max_length=10, verbose_name="Символ валюты"),
        ),
        migrations.AlterField(
            model_name="currency",
            name="ticker",
            field=models.CharField(blank=True, max_length=50, verbose_name="Служебный тикер"),
        ),
        migrations.AlterField(
            model_name="fixing",
            name="indexId",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fixings",
                to="fixings.index",
                verbose_name="Акция",
            ),
        ),
        migrations.AlterField(
            model_name="fixing",
            name="value",
            field=models.DecimalField(
                blank=True,
                decimal_places=12,
                max_digits=30,
                null=True,
                verbose_name="Цена закрытия",
            ),
        ),
        migrations.AlterField(
            model_name="index",
            name="ccyId",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="fixings.currency",
                verbose_name="Валюта акции",
            ),
        ),
        migrations.AlterField(
            model_name="index",
            name="indexISIN",
            field=models.CharField(blank=True, max_length=200, verbose_name="Тикер"),
        ),
        migrations.AlterField(
            model_name="index",
            name="indexName",
            field=models.CharField(blank=True, max_length=200, unique=True, verbose_name="Название акции"),
        ),
    ]
