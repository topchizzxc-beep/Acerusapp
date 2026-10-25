import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import LabeledPrice, PreCheckoutQuery, SuccessfulPayment

# Данные вписаны напрямую в код для быстрого запуска
BOT_TOKEN = '8291306164:AAEyPTn8mrl3jsxwUWHUeAnmwwplNCj_ZcA'
ADMIN_ID = 7386449043 

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

# Словарь с ценами для услуг (название: количество Telegram Stars)
SERVICES = {
    'buy_support': {'title': '✨ ПОДДЕРЖКА ПРОЕКТА', 'price': 5},
    'buy_bot': {'title': '🤖 ЗАКАЗАТЬ БОТА', 'price': 300},
    'buy_design': {'title': '🎨 ДИЗАЙН БАННЕРА', 'price': 100},
    'buy_text': {'title': '📝 ТЕКСТ ЧЕРЕЗ ИИ', 'price': 100}
}


# ================= КЛАВИАТУРЫ (МЕНЮ) =================

def get_main_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text='✨ ПОДДЕРЖКА ПРОЕКТА — 5 ⭐️', callback_data='buy_support')],
        [types.InlineKeyboardButton(text='🤖 ЗАКАЗАТЬ БОТА — 300 ⭐️', callback_data='buy_bot')],
        [types.InlineKeyboardButton(text='🎨 ДИЗАЙН БАННЕРА — 100 ⭐️', callback_data='buy_design')],
        [types.InlineKeyboardButton(text='📝 ТЕКСТ ЧЕРЕЗ ИИ — 100 ⭐️', callback_data='buy_text')],
        [types.InlineKeyboardButton(text='ℹ️ Обо мне', callback_data='press_about'),
         types.InlineKeyboardButton(text='💻 Мой софт', callback_data='press_software')],
        [types.InlineKeyboardButton(text='📞 Написать мне в ЛС', url='https://t.me/Casino_lucker')]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard():
    buttons = [
        [types.InlineKeyboardButton(text='⬅️ НАЗАД В МЕНЮ', callback_data='back_to_main')]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def get_start_data(name: str):
    text = (f"Приветствую, {name}! 👋\nДобро пожаловать в ACERUS IT.\n\n"
            f"Управляйте заказами, выбирайте ИТ-услуги и совершайте безопасную оплату прямо под фото:")
    return text, get_main_keyboard()


# ================= ОБРАБОТЧИКИ КОМАНД =================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text, reply_markup = get_start_data(message.from_user.first_name)
    try:
        photo = types.FSInputFile("about.jpg") 
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=reply_markup
        )
    except Exception:
        await message.answer(text, reply_markup=reply_markup)


# ================= ОБРАБОТКА ОПЛАТЫ (TELEGRAM STARS) =================

@dp.callback_query(F.data.in_(SERVICES.keys()))
async def process_buy_service(callback: types.CallbackQuery):
    service_key = callback.data
    service_data = SERVICES[service_key]
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer_invoice(
        title=service_data['title'],
        description=f"Оплата услуги '{service_data['title']}' через Telegram Stars. Безопасная транзакция.",
        payload=service_key,               
        provider_token="",                 
        currency="XTR",                    
        prices=[
            LabeledPrice(label=service_data['title'], amount=service_data['price'])
        ]
    )
    
    await callback.message.answer(
        text="Вы можете оплатить услугу выше или вернуться назад:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    try:
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        print(f"Ошибка подтверждения платежа: {e}")


@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment_info: SuccessfulPayment = message.successful_payment
    service_key = payment_info.invoice_payload  
    service_title = SERVICES.get(service_key, {}).get('title', 'Услуга')
    
    user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    user_username = f"(@{message.from_user.username})" if message.from_user.username else "(нет юзернейма)"

    await message.answer(
        f"🎉 Спасибо за оплату!\n\n"
        f"Ваш платеж на сумму <b>{payment_info.total_amount} ⭐️</b> за услугу "
        f"<b>«{service_title}»</b> успешно принят.\n\n"
        f"Я свяжусь с вами в ближайшее время для уточнения деталей!",
        reply_markup=get_back_keyboard()
    )
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
                 f"👤 <b>Клиент:</b> {user_mention} {user_username}\n"
                 f"🆔 <b>ID клиента:</b> <code>{message.from_user.id}</code>\n"
                 f"📦 <b>Услуга:</b> {service_title}\n"
                 f"💵 <b>Сумма:</b> {payment_info.total_amount} Telegram Stars ⭐️\n"
                 f"📄 <b>ID платежа:</b> <code>{payment_info.telegram_payment_charge_id}</code>"
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление админу: {e}")


# ================= НАВИГАЦИЯ И ИНФОРМАЦИЯ =================

@dp.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    text, reply_markup = get_start_data(callback.from_user.first_name)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    try:
        photo = types.FSInputFile("about.jpg")
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text=text, reply_markup=reply_markup)
            
    await callback.answer()


@dp.callback_query(F.data == 'press_about')
async def press_about(callback: types.CallbackQuery):
    text = ("ℹ️ <b>Обо мне:</b>\n\n"
            "Я профессиональный IT-разработчик. Создаю Telegram-ботов, "
            "веб-приложения и элементы графического дизайна любой сложности.")
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_keyboard())
    except Exception:
        try:
            await callback.message.edit_text(text=text, reply_markup=get_back_keyboard())
        except Exception:
            await callback.message.answer(text=text, reply_markup=get_back_keyboard())
    await callback.answer()


@dp.callback_query(F.data == 'press_software')
async def press_software(callback: types.CallbackQuery):
    text = ("💻 <b>Мой софт и скрипты:</b>\n\n"
            "• Автоматизация рутинных процессов\n"
            "• Разработка кастомных парсеров данных\n"
            "• Скрипты для работы с API сторонних сервисов\n\n"
            "Вы можете заказать разработку уникального софта через меню или написав мне напрямую!")
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_keyboard())
    except Exception:
        try:
            await callback.message.edit_text(text=text, reply_markup=get_back_keyboard())
        except Exception:
            await callback.message.answer(text=text, reply_markup=get_back_keyboard())
    await callback.answer()


# ================== ВОЗВРАТ СРЕДСТВ (REFUND) =================

@dp.message(Command("paysupport"))
async def cmd_paysupport(message: types.Message):
    text = (
        "ℹ️ <b>Поддержка платежей ACERUS IT</b>\n\n"
        "Если вы хотите вернуть свои Telegram Stars за ошибочный платеж, "
        "вы можете сделать это автоматически прямо сейчас.\n\n"
        "Для этого отправьте боту команду: <code>/refund ID_ПЛАТЕЖА</code>\n\n"
        "<i>(ID платежа можно скопировать в Telegram: Настройки ➡️ Telegram Stars ➡️ История транзакций).</i>"
    )
    await message.answer(text)


@dp.message(Command("refund"))
async def cmd_refund(message: types.Message, bot: Bot):
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(
            "❌ <b>Ошибка!</b> Вы не указали ID платежа.\n"
            "Пример команды: <code>/refund 523764829384</code>"
        )
        return

    # ИСПРАВЛЕНО: берем конкретно элемент списка по индексу 1 и очищаем его от пробелов
    charge_id = args[1].strip()
    user_id = message.from_user.id

    try:
        # Выполняем возврат Telegram Stars пользователю через Telegram API
        await bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id
        )
        
        await message.answer(
            f"✅ <b>Успешный возврат!</b>\n\n"
            f"Платеж <code>{charge_id}</code> успешно аннулирован. "
            f"Telegram Stars возвращены на ваш баланс."
        )
        
        # Уведомляем администратора о том, что был оформлен возврат средств
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"↩️ <b>ОФОРМЛЕН ВОЗВРАТ ЗВЕЗД</b>\n\n"
                     f"👤 <b>Пользователь:</b> ID {user_id}\n"
                     f"📄 <b>ID транзакции:</b> <code>{charge_id}</code>"
            )
        except Exception as admin_err:
            print(f"Не удалось отправить уведомление админу о возврате: {admin_err}")
            
    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка возврата!</b>\n\n"
            f"Не удалось вернуть средства. Проверьте правильность ID платежа. "
            f"Обратите внимание, что оформить возврат можно только в течение 24 дней с момента проведения оплаты.\n\n"
            f"<i>Технический текст ошибки: {e}</i>"
        )


# ================== ЗАПУСК БОТА ==================

async def main():
    print("Бот успешно запущен в режиме Polling и готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
