from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.telegram_service import set_webhook, delete_webhook


class Command(BaseCommand):
    help = "Установить/удалить Telegram webhook"

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true")

    def handle(self, *args, **options):
        if options["delete"]:
            ok = delete_webhook()
            self.stdout.write(f"Webhook удалён: {ok}")
            return

        url = f"{settings.SITE_BASE_URL}/api/auth/support/webhook/telegram/"
        ok = set_webhook(url)
        msg = f"Webhook → {url}"
        self.stdout.write(
            self.style.SUCCESS(msg) if ok else self.style.ERROR(f"ОШИБКА: {msg}")
        )