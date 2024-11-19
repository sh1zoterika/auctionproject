from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Auction, AuctionHistory, AuctionLot, User, AuctionImage
from telegram import Bot
import telebot
from asgiref.sync import sync_to_async, async_to_sync
from django.conf import settings
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import timedelta
from django.db import transaction
import re

bot1 = telebot.TeleBot('7709398639:AAEPSA2BQkkours7twiocFUb244yRsJa9oI')
bot2 = telebot.TeleBot('7574302031:AAGWl2yNEwI1L2cHFfpQLnCZapzVvBpkkBA')
TELEGRAM_CHAT_ID = "-4579059035"


def delete_group_message(auction_id):
    chat_id = '-4579059035'
    auction = Auction.objects.get(id=auction_id)
    message_id = auction.message_id
    bot1.delete_message(chat_id=chat_id, message_id=message_id)


def send_telegram_message(chat_id, message):
    bot2.send_message(chat_id, message)


def set_message_id(message_id, auction_id):
    auction = Auction.objects.get(id=auction_id)
    auction.message_id = message_id
    auction.save()


def get_lots(id):
    try:
        auction = Auction.objects.get(id=id)
        return list(AuctionLot.objects.select_related('user').filter(lot_auction=auction))
    except Auction.DoesNotExist:
        return None

def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

def create_auction(auction_id):
    auction = Auction.objects.get(id=auction_id)
    lots = get_lots(auction.id)
    if lots:
        # Сортировка лотов по величине в убывающем порядке и выбор первых трех
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
        url=f"https://t.me/moneta_active_bot?start=auction_{auction.id}"
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
            auction_message_sent = bot1.send_photo(
                TELEGRAM_CHAT_ID,
                photo,
                caption=auction_message,
                parse_mode='Markdown',
                reply_markup=markup
            )
    else:
        auction_message_sent = bot1.send_message(
            TELEGRAM_CHAT_ID,
            auction_message,
            parse_mode='Markdown',
            reply_markup=markup
        )

    message_id = auction_message_sent.message_id
    set_message_id(message_id, auction.id)


def get_remaining_time(end_time):
    now = timezone.now()
    remaining_time = end_time - now
    if remaining_time > timedelta(seconds=0):
        return str(remaining_time).split(".")[0]
    else:
        return "Аукцион завершен!"


def edit_message(message_id, text, auction_id):
    print("Пытаюсь изменить сообщение")
    chat_id = "-4579059035"
    auction = Auction.objects.get(id=auction_id)


    updated_text = (
        f"{text}\n\n"
    )

    auction_images = AuctionImage.objects.filter(auction=auction)
    first_image_path = None
    if auction_images.exists():
        first_image_path = auction_images.first().image.path

    # Формируем кнопки
    markup = telebot.types.InlineKeyboardMarkup()
    button_bid = telebot.types.InlineKeyboardButton(
        "Сделать ставку",
        url=f"https://t.me/moneta_active_bot?start=auction_{auction.id}"
    )
    button_time = telebot.types.InlineKeyboardButton(
        "🕗",
        callback_data=f"remaining_time_{auction.id}"
    )
    button_info = telebot.types.InlineKeyboardButton(
        "ℹ️",
        callback_data="info_button"
    )
    markup.add(button_bid, button_time, button_info)

    if first_image_path:
        with open(first_image_path, "rb") as photo:
            media = telebot.types.InputMediaPhoto(
                photo,
                caption=updated_text,
                parse_mode="Markdown"
            )
            bot1.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=media,
                reply_markup=markup
            )
    else:
        bot1.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=updated_text,
            parse_mode="Markdown",
            reply_markup=markup
        )


@receiver(post_save, sender=Auction)
def end_auction(sender, instance, **kwargs):
    if instance.end_time <= timezone.now() and instance.active:
        auction_lots = AuctionLot.objects.filter(lot_auction=instance)
        if not auction_lots.exists():
            winner = None
            final_price = None
        else:
            try:
                with transaction.atomic():
                    highest_bid = auction_lots.order_by('-value').first()
                    winner = highest_bid.user
                    final_price = highest_bid.value
                    winner.hold_balance = winner.hold_balance - final_price
                    seller = instance.seller
                    fee = int(float(instance.current_price) * 0.05)
                    seller.balance = seller.balance - fee
                    seller.save()
                    winner.save()
                    other_lots = AuctionLot.objects.filter(lot_auction=instance).exclude(user=winner)
                    if other_lots.exists():
                        for lot in other_lots:
                            user = lot.user
                            user.hold_balance -= lot.value
                            user.balance += lot.value
                            user.save()
            except Exception:
                print('Ошибка при окончании аукциона')

        AuctionHistory.objects.create(
            product_name=instance.product_name,
            geolocation=instance.geolocation,
            final_price=final_price,
            product_type=instance.product_type,
            start_time=instance.start_time,
            seller=instance.seller,
            description=instance.description,
            end_time=instance.end_time,
            winner=winner,
        )

        if winner:
            message = f"🎉 Поздравляем! Вы победили в аукционе: {instance.product_name}. Ваша ставка: {final_price}!"
            send_telegram_message(winner.chat_id, message)
            delete_group_message(instance.id)
        instance.delete()


@receiver(post_save, sender=AuctionLot)
def auction_lot_created(sender, instance, created, **kwargs):
    if created:
        auction = instance.lot_auction

        def get_lots(id):
            try:
                auction = Auction.objects.get(id=id)
                return list(AuctionLot.objects.select_related('user').filter(lot_auction=auction))
            except Auction.DoesNotExist:
                return 'Нету активных ставок'

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

        message = (
            f"🎉 *Аукцион*: {escape_markdown(auction.product_name)}\n"
            f"💰 *Текущая цена*: {escape_markdown(str(auction.current_price))}\n"
            f"📍 *Локация*: {escape_markdown(auction.geolocation)}\n"
            f"🕒 *Конец аукциона*: {escape_markdown(auction.end_time.strftime('%Y-%m-%d %H:%M:%S'))}\n"
            f"Описание: {escape_markdown(auction.description)}\n"
            f"Лоты:\n{escape_markdown(lot_descriptions)}\n"
        )
        message_id = auction.message_id
        auction_id = auction.id
        edit_message(message_id, message, auction_id)


@receiver(post_save, sender=Auction)
def send_auction_message(sender, instance, **kwargs):
    if instance.start_time <= timezone.now() and instance.active and not instance.sent:
        instance.sent = True
        instance.save()
        create_auction(instance.id)
