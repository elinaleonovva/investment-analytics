import json
import os
from django.core.management.base import BaseCommand
from fixings.models import Currency
from django.db import IntegrityError


class Command(BaseCommand):
    help = "Добавляет валюты в БД из файла currencies.json"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), "currencies.json")

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Файл {file_path} не найден!"))
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Ошибка при чтении JSON файла: {e}"))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка при чтении файла: {e}"))
            return

        currencies = data.get("currencies", [])
        created_count = 0
        existing_count = 0

        for currency_data in currencies:
            try:
                currency, created = Currency.objects.get_or_create(
                    currency=currency_data["currency"],
                    defaults={
                        "symbol": currency_data["symbol"],
                        "ticker": "" if currency_data["currency"] == "USD" else f"{currency_data['currency']}USD=X"
                    }
                )
                if created:
                    created_count += 1
                else:
                    existing_count += 1
            except IntegrityError:
                self.stdout.write(self.style.WARNING(
                    f"Валюта {currency_data['currency']} уже существует с другими параметрами."
                ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Ошибка при создании валюты {currency_data['currency']}: {e}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Добавлено {created_count} новых валют. {existing_count} валют уже существовало."
        ))
