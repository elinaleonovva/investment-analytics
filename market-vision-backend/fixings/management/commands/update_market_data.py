from django.core.management.base import BaseCommand

from fixings.services.market_data import MarketUpdaterService


class Command(BaseCommand):
    help = "Периодическое обновление данных рынка (CurrencyLayer + Yahoo Finance)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-back",
            type=int,
            default=30,
            help="На сколько дней назад догружать историю по акциям",
        )

    def handle(self, *args, **kwargs):
        updater = MarketUpdaterService()
        updater.update_market_data(days_back=kwargs["days_back"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Обновление завершено. История акций обновлена за {kwargs['days_back']} дней."
            )
        )
