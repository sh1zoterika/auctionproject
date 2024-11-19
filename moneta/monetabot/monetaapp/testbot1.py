import os
import telebot
import sys
import django
from django.utils import timezone
from asgiref.sync import sync_to_async
import re
from django.conf import settings

sys.path.append('D:/pythonProject/moneta/monetabot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monetabot.settings')
if not settings.configured:
    django.setup()

from monetaapp.models import Auction, AuctionLot, AuctionImage

TELEGRAM_BOT_TOKEN = "7709398639:AAEPSA2BQkkours7twiocFUb244yRsJa9oI"
TELEGRAM_CHAT_ID = "-4579059035"
SECOND_BOT_USERNAME = 'moneta_active_bot'

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_active_auctions():
    return list(Auction.objects.filter(active=True))


def set_message_id(message_id, auction_id):
    auction = Auction.objects.get(id=auction_id)
    auction.message_id = message_id
    auction.save()


def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


def get_lots(id):
    try:
        auction = Auction.objects.get(id=id)
        return list(AuctionLot.objects.select_related('user').filter(lot_auction=auction))
    except Auction.DoesNotExist:
        return None


def get_remaining_time(end_time):
    now = timezone.now()
    remaining_time = end_time - now

    remaining_seconds = int(remaining_time.total_seconds())

    if remaining_seconds <= 0:
        return "Время истекло!"

    hours = remaining_seconds // 3600
    minutes = (remaining_seconds % 3600) // 60
    seconds = remaining_seconds % 60
    return f"{hours}ч {minutes}м {seconds}с"


def send_active_auctions(message):
    active_auctions = get_active_auctions()

    for auction in active_auctions:
        lots = get_lots(auction.id)
        if lots:
            top_lots = sorted(lots, key=lambda lot: lot.value, reverse=True)[:3]
            lot_descriptions = "\n".join(
                [
                    f"Место {index + 1}: Лот - {lot.value} пользователя {lot.user.username if lot.user else 'Не указан'}"
                    for index, lot in enumerate(top_lots)
                ]
            )
        else:
            lot_descriptions = 'Нету активных ставок'

        auction_message = (
            f"🎉 *Аукцион*: {escape_markdown(auction.product_name)}\n"
            f"💰 *Текущая цена*: {escape_markdown(str(auction.current_price))}\n"
            f"📍 *Локация*: {escape_markdown(auction.geolocation)}\n"
            f"🕒 *Конец аукциона*: {escape_markdown(auction.end_time.strftime('%Y-%m-%d %H:%M:%S'))}\n"
            f"Описание: {escape_markdown(auction.description)}\n"
            f"Лоты:\n{escape_markdown(lot_descriptions)}\n"
        )

        auction_images = AuctionImage.objects.filter(auction=auction)
        first_image_path = None
        if auction_images.exists():
            first_image_path = auction_images.first().image.path

        markup = telebot.types.InlineKeyboardMarkup()
        button_bid = telebot.types.InlineKeyboardButton(
            "Сделать ставку",
            url=f"https://t.me/{SECOND_BOT_USERNAME}?start=auction_{auction.id}"
        )
        button_time = telebot.types.InlineKeyboardButton(
            "🕗",
            callback_data=f"remaining_time_{auction.id}"
        )
        button_info = telebot.types.InlineKeyboardButton(
            "ℹ️",
            callback_data='info_button'
        )
        markup.add(button_bid, button_time, button_info)

        if first_image_path:
            with open(first_image_path, 'rb') as photo:
                auction_message_sent = bot.send_photo(
                    TELEGRAM_CHAT_ID,
                    photo,
                    caption=auction_message,
                    parse_mode='Markdown',
                    reply_markup=markup
                )
        else:
            auction_message_sent = bot.send_message(
                TELEGRAM_CHAT_ID,
                auction_message,
                parse_mode='Markdown',
                reply_markup=markup
            )

        message_id = auction_message_sent.message_id
        set_message_id(message_id, auction.id)


@bot.message_handler(commands=['auctions'])
def handle_auctions(message):
    send_active_auctions(message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("remaining_time_"))
def handle_remaining_time(call):
    auction_id = int(call.data.split("_")[2])
    auction = Auction.objects.get(id=auction_id)
    remaining_time = get_remaining_time(auction.end_time)

    bot.answer_callback_query(call.id, f"Оставшееся время до конца аукциона: {remaining_time}", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("info_button"))
def handle_remaining_time(call):
    bot.answer_callback_query(call.id,
                              f"читы — бан, кемперство — бан, оскорбления — бан, оскорбление администрации — расстрел, потом бан",
                              show_alert=True)


def main():
    print('запускаю бота 1')
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()
