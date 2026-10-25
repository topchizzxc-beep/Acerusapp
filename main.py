import os  # Встроенный модуль для работы с операционной системой
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from dotenv import load_file, load_dotenv  # Импортируем dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Теперь вместо текста мы безопасно берем данные из окружения компьютера
BOT_TOKEN = os.getenv('8291306164:AAHOKPsqcOJNiMiVoQBVKhh54PMSYyCNHys')
# Так как ID — это число, обязательно превращаем его из текста в int
ADMIN_ID = int(os.getenv('7386449043')) 

# Дальше твой код идет без изменений...
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

# ================= ОБРАБОТКА ОПЛАТЫ (TELEGRAM STARS) =================

# 1. ОТПРАВКА ИНВОЙСА ПРИ НАЖАТИИ НА КНОПКУ КУПИТЬ
@dp.callback_query(F.data.in_(SERVICES.keys()))
async def process_buy_service(callback: types.CallbackQuery):
    service_key = callback.data
    service_data = SERVICES[service_key]
    
    # Удаляем старое меню, чтобы не забивать чат
    await callback.message.delete()
    
    # Отправляем ЧИСТЫЙ инвойс без принудительного reply_markup
    # Telegram сам добавит кнопку "Оплатить {price} XTR"
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
    
    # Чтобы пользователь не застрял в инвойсе, отправляем кнопку "Назад" отдельным сообщением прямо под ним
    await callback.message.answer(
        text="Вы можете оплатить услугу выше или вернуться назад:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


# 2. ПОДТВЕРЖДЕНИЕ ПЛАТЕЖА (PreCheckoutQuery) - Должен быть без фильтров!
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    try:
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        print(f"Ошибка подтверждения платежа: {e}")


# 3. ФИКСАЦИЯ УСПЕШНОГО ПЛАТЕЖА + УВЕДОМЛЕНИЕ АДМИНА
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

# Переместили кнопку "Назад" повыше информационных кнопок
@dp.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    text, reply_markup = get_start_data(callback.from_user.first_name)
    
    # Полностью удаляем всё, что было (сообщение-заглушку инвойса или инфо-текст)
    # и отправляем чистое главное меню с картинкой с нуля. Это самый надежный способ.
    await callback.message.delete()
    try:
        photo = types.FSInputFile("about.jpg")
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text=text, reply_markup=reply_markup)
            
    await callback.answer()



# ================= НАВИГАЦИЯ И ИНФОРМАЦИЯ =================

@dp.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: types.CallbackQuery):
    text, reply_markup = get_start_data(callback.from_user.first_name)
    
    try:
        await callback.message.edit_text(text=text, reply_markup=reply_markup)
    except Exception:
        await callback.message.delete()
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
        await callback.message.edit_text(text=text, reply_markup=get_back_keyboard())
    await callback.answer()


@dp.callback_query(F.data == 'press_software')
async def press_software(callback: types.CallbackQuery):
    text = ("💻 <b>Мой софт:</b>\n\n"
            "Актуальные проекты:\n"
            "• Бот-конструктор интерактивных меню\n"
            "• ИИ-генератор продающих текстов\n"
            "• Умные CRM-системы автоматизации")
    try:
        await callback.message.edit_caption(caption=text, reply_markup=get_back_keyboard())
    except Exception:
        await callback.message.edit_text(text=text, reply_markup=get_back_keyboard())
    await callback.answer()

from aiogram.filters import Command, CommandObject

# ================= КОМАНДА ВОЗВРАТА СРЕДСТВ ДЛЯ АДМИНА (REFUND) =================

@dp.message(Command("refund"))
async def cmd_refund(message: types.Message, command: CommandObject):
    # 1. Защита: проверяем, что команду ввёл именно администратор проекта
    if message.from_user.id != ADMIN_ID:
        # Обычным пользователям просто ничего не отвечаем или пишем, что команда не найдена
        return 

    # 2. Проверяем, переданы ли аргументы (ID пользователя и ID платежа)
    if not command.args or len(command.args.split()) < 2:
        await message.answer(
            "❌ <b>Ошибка:</b> Неверный формат команды.\n\n"
            "Используйте формат:\n"
            "<code>/refund ИД_ПОЛЬЗОВАТЕЛЯ ИД_ПЛАТЕЖА</code>\n\n"
            "<i>Пример: /refund 7386449043 54321_abc</i>"
        )
        return

    # Разделяем аргументы по пробелу
    args = command.args.split()
    target_user_id = int(args[0])  # Кому возвращаем (превращаем в число)
    charge_id = args[1]            # ID транзакции

    try:
        # Вызываем официальный метод Telegram для возврата Stars
        await bot.refund_star_payment(
            user_id=target_user_id,
            telegram_payment_charge_id=charge_id
        )
        
        # Отчёт тебе в чат
        await message.answer(
            f"✅ <b>Возврат успешно выполнен!</b>\n\n"
            f"👤 <b>Кому:</b> Клиенту с ID <code>{target_user_id}</code>\n"
            f"📄 <b>Транзакция:</b> <code>{charge_id}</code>\n\n"
            f"Telegram Stars были мгновенно списаны с баланса твоего бота и вернулись пользователю."
        )

        # Автоматически отправляем уведомление самому пользователю, чтобы он знал о возврате
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=f"🔄 <b>Уведомление о возврате</b>\n\n"
                     f"Администратор произвёл возврат Telegram Stars за вашу покупку.\n"
                     f"Транзакция ID: <code>{charge_id}</code>\n\n"
                     f"Звёзды уже вернулись на ваш баланс Telegram! Спасибо, что выбираете ACERUS IT."
            )
        except Exception:
            print("Пользователь заблокировал бота, не удалось отправить ему уведомление в ЛС.")
            
    except Exception as e:
        # Если Telegram вернул ошибку (например, неверный ID или прошло более 30 дней)
        await message.answer(
            f"❌ <b>Не удалось выполнить возврат.</b>\n\n"
            f"Проверь данные. Ошибка API: <code>{e}</code>"
        )

#================== ПОДДЕРЖКА ================#
@dp.message(Command("paysupport"))
async def cmd_paysupport(message: types.Message):
    await message.answer(
        "👋 <b>Служба поддержки платежей ACERUS IT</b>\n\n"
        "Если у вас возникли проблемы с оплатой или вы хотите оформить возврат, "
        "используйте команду <code>/refund ИД_ПЛАТЕЖА</code> или напишите мне в личные сообщения."
    )


# ================= ЗАПУСК БОТА =================

async def main():
    print("Бот успешно запущен и готов к продажам!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
