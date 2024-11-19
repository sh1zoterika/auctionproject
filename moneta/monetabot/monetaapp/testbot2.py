import os
import sys
import django
import telebot
from django.conf import settings
from django.db.models.signals import post_save
from django.utils import timezone
from asgiref.sync import sync_to_async
import re
from django.db import transaction
from django.conf import settings

sys.path.append('D:/pythonProject/moneta/monetabot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monetabot.settings')
if not settings.configured:
    django.setup()

from monetaapp.models import Auction, AuctionLot, User, AuctionImage, AuctionFiles, AutoBid

TELEGRAM_BOT2_TOKEN = '7574302031:AAGWl2yNEwI1L2cHFfpQLnCZapzVvBpkkBA'

bot = telebot.TeleBot(TELEGRAM_BOT2_TOKEN)


def get_username(chat_id):
    user = User.objects.get(chat_id=chat_id)
    return user.username


def check_or_create_user(chat_id, username):
    print(username)
    user, created = User.objects.get_or_create(
        chat_id=chat_id,
        defaults={'username': username,
                  'password': 'pbkdf2_sha256$600000$4Lb7uGTHBDY0dHEwbPnOhH$ckwq85lAVLqcjdivC4JqAvyc/IHTtZO/euj5yDXBaMA=',
                  'type': 'user', 'balance': 0, 'succesful_trades': 0}
    )
    return user


def get_auction_by_id(auction_id):
    try:
        return Auction.objects.get(id=auction_id)
    except Auction.DoesNotExist:
        return None


def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    username = str(message.chat.username)
    user = check_or_create_user(chat_id, username)
    if user.status == 'inactive':
        bot.send_message(message.chat.id, "Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return
    args = message.text.split()
    if not args or not args[1].startswith("auction_"):
        bot.send_message(message.chat.id, "Аукцион не найден.")
        return

    auction_id = int(args[1].split("_")[1])
    auction = get_auction_by_id(auction_id)
    if not auction:
        bot.send_message(message.chat.id, "Аукцион не найден.")
        return

    message_text = (
        f"🎉 *Аукцион*: {escape_markdown(auction.product_name)}\n"
        f"💰 *Текущая цена*: {escape_markdown(str(auction.current_price))}\n"
        f"📍 *Локация*: {escape_markdown(auction.geolocation)}\n"
        f"🕒 *Конец аукциона*: {escape_markdown(auction.end_time.strftime('%Y-%m-%d %H:%M:%S'))}\n"
        f"Описание: {escape_markdown(auction.description)}\n"
    )

    # Кнопки
    if user.succesful_trades >= 10:
        markup = telebot.types.InlineKeyboardMarkup()
        button_auto_bid = telebot.types.InlineKeyboardButton(
            "Настроить авто-ставку", callback_data=f"auto_bid_{auction.id}")
        button_bid = telebot.types.InlineKeyboardButton(
            "Сделать ставку", callback_data=f"make_bid_{auction.id}_{chat_id}")
        button_account = telebot.types.InlineKeyboardButton(
            "Личный кабинет", callback_data=f"personal_account_{chat_id}_{username}")
        button_files = telebot.types.InlineKeyboardButton('Приложенные файлы',
                                                          callback_data=f'get_files_{auction.id}_{chat_id}')
        button_custom_bid = telebot.types.InlineKeyboardButton(
            "Сделать свою ставку", callback_data=f"custom_bid_{auction.id}_{chat_id}")
        markup.add(button_bid, button_account, button_files, button_auto_bid, button_custom_bid)
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        button_bid = telebot.types.InlineKeyboardButton(
            "Сделать ставку", callback_data=f"make_bid_{auction.id}_{chat_id}")
        button_account = telebot.types.InlineKeyboardButton(
            "Личный кабинет", callback_data=f"personal_account_{chat_id}_{username}")
        button_files = telebot.types.InlineKeyboardButton('Приложенные файлы',
                                                          callback_data=f'get_files_{auction.id}_{chat_id}')
        button_custom_bid = telebot.types.InlineKeyboardButton(
            "Сделать свою ставку", callback_data=f"custom_bid_{auction.id}_{chat_id}")
        markup.add(button_bid, button_account, button_files, button_custom_bid)

    # Проверяем изображения
    auction_images = AuctionImage.objects.filter(auction=auction)
    if auction_images.exists():
        media_group = []
        for image in auction_images:
            image_path = image.image.path
            media_group.append(telebot.types.InputMediaPhoto(open(image_path, "rb")))

        media_group[0].caption = message_text
        media_group[0].parse_mode = "Markdown"

        bot.send_media_group(
            chat_id=message.chat.id,
            media=media_group,
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Вы можете сделать ставку или открыть личный кабинет:",
            reply_markup=markup
        )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text=message_text,
            parse_mode="Markdown",
            reply_markup=markup
        )


def create_bid(auction_id, chat_id):
    user = User.objects.get(chat_id=chat_id)
    auction = Auction.objects.get(id=auction_id)
    value = auction.current_price + 100
    lot = AuctionLot.objects.get(user=user, lot_auction=auction)
    try:
        with transaction.atomic():
            if user.balance + lot.value >= value:
                auction.current_price = value
                auction.save()
                user.balance = user.balance + lot.value - value
                user.hold_balance = user.hold_balance - lot.value + value
                lot.delete()
                user.save()
                new_lot = AuctionLot.objects.create(lot_auction=auction, user=user, value=value)

                auto_bids = AutoBid.objects.filter(auction=auction, active=True).exclude(user=user)
                for auto_bid in auto_bids:
                    if auto_bid.max_bid >= auction.current_price + 100:
                        create_bid(auction.id, auto_bid.user.chat_id)
                        break

                return new_lot
            else:
                return None
    except Exception:
        return None


@bot.callback_query_handler(func=lambda call: call.data.startswith("make_bid_"))
def handle_bid(call):
    callback_data = call.data.split("_")
    auction_id = int(callback_data[2])
    chat_id = callback_data[3]
    user = User.objects.get(chat_id=chat_id)
    if user.status == 'inactive':
        bot.send_message(chat_id, "Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return
    bid = create_bid(auction_id, chat_id)
    username = get_username(chat_id)
    markup = telebot.types.InlineKeyboardMarkup()
    button_account = telebot.types.InlineKeyboardButton(
        "Личный кабинет", callback_data=f"personal_account_{chat_id}_{username}")
    markup.add(button_account)

    if bid:
        bot.send_message(
            call.message.chat.id,
            text=f"Ваша ставка успешно принята на аукцион: {bid.lot_auction.product_name} с новой ценой {bid.value}!",
            reply_markup=markup, parse_mode='Markdown'
        )

    else:
        bot.send_message(
            call.message.chat.id,
            text='Недостаточно средств на балансе',
            reply_markup=markup, parse_mode='Markdown'
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("personal_account_"))
def handle_personal_account(call):
    print(call.data)
    chat_id = call.data.split("_")[2]
    username = call.data.split("_")[3]
    user = check_or_create_user(chat_id, username)

    message = (
        f"🛠 Ваш личный кабинет:\n"
        f"🔑 *Логин*: {escape_markdown(user.username)}\n"
        f"🔒 *Пароль*: root\n"
        f"🔒 *Баланс*: {escape_markdown(str(user.balance))}\n"
        f"🔒 *Баланс на удержании*: {escape_markdown(str(user.hold_balance))}\n"
        f"🔗 *Ссылка на вход*: [Перейти в личный кабинет](http://127.0.0.1:8000/login)"
    )

    bot.send_message(call.message.chat.id, text=message, parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: call.data.startswith("get_files_"))
def get_files(call):
    print(call.data)
    auction_id = call.data.split('_')[2]
    chat_id = call.data.split('_')[3]
    auction = Auction.objects.get(id=auction_id)
    files = AuctionFiles.objects.filter(auction=auction)

    if files.exists():
        for auction_file in files:
            file_path = auction_file.file.path
            print(file_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                if os.path.getsize(file_path) > 0:
                    with open(file_path, "rb") as file:
                        bot.send_document(chat_id, file)
                else:
                    bot.send_message(chat_id, "Файл существует, но он пуст.")
            else:
                bot.send_message(chat_id, f"Файл не найден по пути: {file_path}")
    else:
        bot.send_message(chat_id, "Файлы не найдены.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("auto_bid_"))
def handle_auto_bid(call):
    callback_data = call.data.split("_")
    auction_id = int(callback_data[2])
    chat_id = call.message.chat.id

    bot.send_message(
        chat_id,
        "Введите максимальную сумму, до которой вы готовы делать авто-ставки:"
    )

    bot.register_next_step_handler(
        call.message,
        set_auto_bid,
        auction_id=auction_id
    )


def set_auto_bid(message, auction_id):
    chat_id = message.chat.id
    try:
        max_bid = float(message.text)
        user = User.objects.get(chat_id=chat_id)
        auction = Auction.objects.get(id=auction_id)

        auto_bid, created = AutoBid.objects.update_or_create(
            user=user,
            auction=auction,
            defaults={'max_bid': max_bid, 'active': True}
        )

        bot.send_message(
            chat_id,
            f"Авто-ставка успешно настроена. Максимальная сумма: {max_bid}."
        )
    except ValueError:
        bot.send_message(chat_id, "Ошибка! Введите число.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("custom_bid_"))
def handle_custom_bid(call):
    callback_data = call.data.split("_")
    auction_id = int(callback_data[2])
    chat_id = call.message.chat.id

    user = User.objects.get(chat_id=chat_id)
    if user.status == 'inactive':
        bot.send_message(chat_id, "Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return

    auction = Auction.objects.get(id=auction_id)
    min_bid = auction.current_price + 100

    bot.send_message(
        chat_id,
        f"Введите сумму ставки. Минимальная сумма: {min_bid}"
    )

    bot.register_next_step_handler(call.message, process_custom_bid, auction_id)


def process_custom_bid(message, auction_id):
    chat_id = message.chat.id
    user = User.objects.get(chat_id=chat_id)
    auction = Auction.objects.get(id=auction_id)
    min_bid = auction.current_price + 100
    try:
        value = int(message.text)

        if value < min_bid:
            bot.send_message(chat_id, f"Ошибка! Ставка должна быть не меньше {min_bid}.")
            return
    except ValueError:
        bot.send_message(chat_id, "Ошибка! Введите число.")

    lot = AuctionLot.objects.get(user=user, lot_auction=auction)
    try:
        with transaction.atomic():
            if user.balance + lot.value >= value:
                auction.current_price = value
                auction.save()
                user.balance = user.balance + lot.value - value
                user.hold_balance = user.hold_balance - lot.value + value
                lot.delete()
                user.save()
                new_lot = AuctionLot.objects.create(lot_auction=auction, user=user, value=value)

                auto_bids = AutoBid.objects.filter(auction=auction, active=True).exclude(user=user)
                for auto_bid in auto_bids:
                    if auto_bid.max_bid >= auction.current_price + 100:
                        create_bid(auction.id, auto_bid.user.chat_id)
                        break
                bot.send_message(
                    chat_id,
                    f"Ваша ставка на аукцион '{auction.product_name}' успешно принята. Сумма: {value}."
                )
                return new_lot
            else:
                return None
    except Exception:
        bot.send_message(chat_id, f"Произошла ошибка! Попробуйте ещё раз")
        return


def main():
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()
