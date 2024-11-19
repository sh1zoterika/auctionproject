import os
import telegram
from django.core.management.base import BaseCommand
from django.utils import timezone
from monetaapp.models import Auction

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class Command(BaseCommand):
    help = "Posts active auctions to the Telegram group."

    def handle(self, *args, **kwargs):
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        active_auctions = Auction.objects.filter(active=True, end_time__gte=timezone.now())

        for auction in active_auctions:
            message = (
                f"🎉 *Аукцион*: {auction.product_name}\n"
                f"💰 *Текущая цена*: {auction.current_price}\n"
                f"📍 *Локация*: {auction.geolocation}\n"
                f"🕒 *Конец аукциона*: {auction.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Описание: {auction.description}"
            )
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)