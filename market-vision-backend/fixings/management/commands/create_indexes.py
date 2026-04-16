import json
import os
from django.core.management.base import BaseCommand
from fixings.models import Index, Currency
from django.db import IntegrityError


class Command(BaseCommand):
    help = "Добавляет акции в БД из файла indexes.json"

    def handle(self, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), "indexes.json")

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

        indexes = data.get("indexes", [])
        created_count = 0
        existing_count = 0
        error_count = 0

        for index in indexes:
            try:
                # Get the currency first
                ccyId = Currency.objects.filter(currency=index["ccyId"]).first()
                if not ccyId:
                    self.stdout.write(self.style.WARNING(
                        f"Валюта {index['ccyId']} не найдена для акции {index['indexName']}. Пропускаем."
                    ))
                    error_count += 1
                    continue

                # Try to create or get the index
                stock, created = Index.objects.get_or_create(
                    indexName=index["indexName"],
                    defaults={
                        "ccyId": ccyId,
                        "indexISIN": index["indexISIN"]
                    }
                )
                if created:
                    created_count += 1
                else:
                    existing_count += 1
                    # Update the index if it exists but has different data
                    if stock.ccyId != ccyId or stock.indexISIN != index["indexISIN"]:
                        stock.ccyId = ccyId
                        stock.indexISIN = index["indexISIN"]
                        stock.save()
                        self.stdout.write(self.style.WARNING(
                            f"Акция {index['indexName']} обновлена с новыми данными."
                        ))

            except IntegrityError:
                self.stdout.write(self.style.WARNING(
                    f"Акция {index['indexName']} уже существует с другими параметрами."
                ))
                error_count += 1
            except KeyError as e:
                self.stdout.write(self.style.WARNING(
                    f"Отсутствует обязательное поле {e} для акции {index.get('indexName', 'Unknown')}."
                ))
                error_count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Ошибка при создании акции {index.get('indexName', 'Unknown')}: {e}"
                ))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Добавлено {created_count} новых акций. "
            f"{existing_count} акций уже существовало. "
            f"{error_count} ошибок при обработке."
        ))
