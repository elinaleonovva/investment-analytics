from django.core.management.base import BaseCommand

from fixings.models import Metal


DEFAULT_METALS = [
    {"code": "XAU", "name": "Gold", "symbol": "Au"},
    {"code": "XAG", "name": "Silver", "symbol": "Ag"},
    {"code": "XPT", "name": "Platinum", "symbol": "Pt"},
    {"code": "XPD", "name": "Palladium", "symbol": "Pd"},
]


class Command(BaseCommand):
    help = "Добавляет базовый список драгоценных металлов."

    def handle(self, *args, **kwargs):
        created = 0
        for item in DEFAULT_METALS:
            _, was_created = Metal.objects.get_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "symbol": item["symbol"],
                },
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Металлы синхронизированы. Добавлено новых записей: {created}."
            )
        )
