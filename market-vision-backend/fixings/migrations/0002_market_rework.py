# Generated manually for market rework

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fixings", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="currencyusdfixing",
            old_name="valueUSD",
            new_name="rate_from_usd",
        ),
        migrations.AlterField(
            model_name="currencyusdfixing",
            name="rate_from_usd",
            field=models.DecimalField(
                blank=True,
                decimal_places=12,
                max_digits=30,
                null=True,
                verbose_name="Курс USD -> валюта",
            ),
        ),
        migrations.CreateModel(
            name="Metal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=10, unique=True, verbose_name="Код металла")),
                ("name", models.CharField(max_length=100, verbose_name="Название")),
                ("symbol", models.CharField(blank=True, max_length=10, verbose_name="Символ")),
            ],
            options={
                "verbose_name": "Драгоценный металл",
                "verbose_name_plural": "Драгоценные металлы",
            },
        ),
        migrations.CreateModel(
            name="MetalUSDFixing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fixingDate", models.DateField(verbose_name="Дата фиксинга")),
                (
                    "rate_from_usd",
                    models.DecimalField(decimal_places=12, max_digits=30, verbose_name="Курс USD -> металл"),
                ),
                (
                    "metal",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fixings", to="fixings.metal"),
                ),
            ],
            options={
                "verbose_name": "Фиксинг металла",
                "verbose_name_plural": "Фиксинги металлов",
            },
        ),
    ]
