
TOKEN = "YOUR TOKEN"

import json
from typing import Dict, Any
import os
from datetime import date, timedelta
import logging
from telegram.constants import ChatMemberStatus
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler, 
)

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для состояний разговора
BROADCAST_MESSAGE, SELECTING_LANGUAGE, SELECTING_SPORT, SELECTING_MENU, REGISTRATION, FIO, SELECTING_DAY, FEEDBACK, BROADCAST_MESSAGE = range(9)

CHECKING_SUBSCRIPTION = range(10, 11)

# Клавиатура для выбора языка
language_keyboard = [
    ["English", "Русский"] 
]
language_markup = ReplyKeyboardMarkup(language_keyboard, one_time_keyboard=True)

sport_keyboard = [
    ['Скейтбординг', 'Лонгбординг'],
    ['Самокат', 'Квады'],
    ['Роллер фристайл'],
    ['Настройки']
]
ru_sport_markup = ReplyKeyboardMarkup(sport_keyboard, one_time_keyboard=True)

Sports_ru = ["Скейтбординг", "Лонгбординг", "Самокат", "Квады", "Роллер фристайл"]

sport_keyboard = [
    ['Skateboarding', 'Longboarding'],
    ['Scooter', 'Quads'],
    ['Inline freestyle'],
    ['Settings']
]
en_sport_markup = ReplyKeyboardMarkup(sport_keyboard, one_time_keyboard=True)

Sports_en = ["Skateboarding", "Longboarding", "Scooter", "Quads", "Inline freestyle"]

Sport_bef = ["Skateboarding", "Longboarding", "Scooter", "Quads", "Aggressive Rollers"]

ru_menu_keyboard = [
    ['Полное расписание', 'Расписание на завтра'],
    ['Фотоотчет'],
    ['Настройки','Главное меню'],
    ['Обратная связь']
]
ru_menu_markup = ReplyKeyboardMarkup(ru_menu_keyboard, one_time_keyboard=True)

en_menu_keyboard = [
    ['Full schedule', 'Tomorrow`s schedule'],
    ['Photos'],
    ['Settings','Main menu'],
    ['Feedback']
]
en_menu_markup = ReplyKeyboardMarkup(en_menu_keyboard, one_time_keyboard=True)

ru_confirm_keyboard = [
    ['Подтверждаю', 'Ввести заново'],
    ['назад']
    ]
ru_confirm_markup = ReplyKeyboardMarkup(ru_confirm_keyboard, one_time_keyboard=True)

en_confirm_keyboard = [
    ['Confirm', 'Reset'],
    ['Back']
    ]
en_confirm_markup = ReplyKeyboardMarkup(en_confirm_keyboard, one_time_keyboard=True)

CHANNEL_ID = "" #CHANEL FOR FEEDBACK
Main_CHANNEL_ID = '' #MAIN CHANNEL
ADMIN_IDS = [] #ADMINS FOR NEWSLETTER (YOU CAN WRITE MORE THEN ONE ADMIN LIKE THIS: [FIRS ADMINS ID, SECOND ADMINS ID, etc.])

def save_user_data(user_data: Dict[str, Any]):
   
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []
    
    # Проверяем, есть ли уже пользователь
    user_exists = False
    for user in users:
        if user['user_id'] == user_data['user_id']:
            user.update(user_data)  # Обновляем данные
            user_exists = True
            break
    
    if not user_exists:
        users.append(user_data)
    
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

USER_DATA_TEMPLATE = {
    "user_id": None,
    "sport": None
}

def get_user_data(user_id: int) -> Dict[str, Any]:
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
            for user in users:
                if user['user_id'] == user_id:
                    return user
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return USER_DATA_TEMPLATE.copy()

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    if update.message.text == 'Отменить':
        await update.message.reply_text("❌ Рассылка отменена", reply_markup=ru_menu_markup
        )
    
        return SELECTING_MENU
    
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        await update.message.reply_text("❌ Нет данных о пользователях.", reply_markup=ru_menu_markup
        )
        return SELECTING_MENU

    bot = Bot(token=TOKEN)
    success = 0
    failed = 0

    event = context.user_data.get('event','рассылка по спорту')

    Sports_en = ["Skateboarding", "Longboarding", "Scooter", "Quads", "Aggressive Rollers"]

    if event == 'рассылка по спорту':
        Sport = context.user_data.get('Sport','Skateboarding')
        Sports_en = [str(Sport)]

    for user in users:
        if user['sport'] in Sports_en:
            try:
                if update.message.text:
                    await bot.send_message(user['user_id'], update.message.text)
                elif update.message.photo:
                    await bot.send_photo(user['user_id'], update.message.photo[-1].file_id)
                elif update.message.document:
                    await bot.send_document(user['user_id'], update.message.document.file_id)
                success += 1
            except Exception as e:
                logger.error(f"Ошибка отправки для {user['user_id']}: {e}")
                failed += 1

    await update.message.reply_text(
        f"✅ Рассылка завершена:\nУспешно: {success}\nНе удалось: {failed}",
        reply_markup=ru_menu_markup
    )
    
    return SELECTING_MENU

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
   
    await update.message.reply_text("❌ Рассылка отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def is_user_subscribed(bot: Bot, user_id: int, channel_username: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
    except Exception as e:
        logger.warning(f"Ошибка при проверке подписки: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:


    user = update.message.from_user
    bot = context.bot

    subscribed = await is_user_subscribed(bot, user.id, "YOUR CHANNEL")
    if not subscribed:
        await update.message.reply_text(
            "❗️Для использования бота необходимо подписаться на канал: https://t.me/CHANNEL \n" \
            "❗️To use the bot, you need to subscribe to the channel: https://t.me/CHANNEL",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Подписаться \ Subscribe", url="https://t.me/CHANNEL")],
                [InlineKeyboardButton("Я подписался \ I subscribed", callback_data="check_subscription")]
            ])
        )
        return CHECKING_SUBSCRIPTION

    await update.message.reply_text(
        "Пожалуйста, выберите язык / Please select your language:",
        reply_markup=language_markup,
    )
    return SELECTING_LANGUAGE

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    bot = context.bot

    subscribed = await is_user_subscribed(bot, user.id, "YOUR CHANNEL")
    if subscribed:
        await query.message.reply_text(
            "✅ Пожалуйста, выберите язык / Please select your language:",
            reply_markup=language_markup
        )
        return SELECTING_LANGUAGE
    else:
        await query.message.reply_text(
            "❗️Вы все еще не подписаны на канал. Подпишитесь и нажмите 'Я подписался' \n " \
            "❗️You are still not subscribed to the channel. Subscribe and click 'I subscribed'",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Подписаться \ Subscribe", url="https://t.me/CHANNEL")],
                [InlineKeyboardButton("Я подписался \ I subscribed", callback_data="check_subscription")]
            ])
        )
        return CHECKING_SUBSCRIPTION



async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    Fio = context.user_data.get('FIO','NN')
    Number = context.user_data.get('Number','NN')
    language = context.user_data.get('language', 'English')


    if update.message.text in ['Назад','Back']:
        if language == 'Russian':
            await update.message.reply_text(
            'Предоставьте номер \n Вы можете отправить его с помощью кнопки ниже или ввести вручную в формате +79123456789.',
            reply_markup=ReplyKeyboardMarkup(
                [[{"text": "Отправить номер телефона", "request_contact": True}],['Назад']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        else:
            await update.message.reply_text(
            'Provide the number \n You can send it using the button below or enter it manually in the format +79123456789.',
            reply_markup=ReplyKeyboardMarkup(
                [[{"text": "Отправить номер телефона", "request_contact": True}],['Back']],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )

        return FIO

    feedback_text = (
        f"📢 *Новый фидбек*\n"
        f"👤 *ФИО:* {Fio}\n"
        f"📞 *Телефон:* {Number}\n"
        f"✉️ *Сообщение:*\n{update.message.text}"
    )

    # Отправляем в канал
    bot = Bot(token=TOKEN)

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=feedback_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в канал: {e}")

    if language == 'Russian':
        await update.message.reply_text(
            f"Сообщение отправлено",
            reply_markup=ru_menu_markup,
        )
    else:
        await update.message.reply_text(
            f"Message sent",
            reply_markup=en_menu_markup,
        )
    return SELECTING_MENU
    

async def Get_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language', 'English')
    user = update.message.from_user

    if update.message.text in ['Назад','Back']:
        if language == 'Russian':
            await update.message.reply_text(
                f"Меню",
                reply_markup=ru_menu_markup,
            )
        else:
            await update.message.reply_text(
                f"Menu",
                reply_markup=en_menu_markup,
            )
        return SELECTING_MENU

    context.user_data['FIO'] = update.message.text

    if language == 'Russian':
        await update.message.reply_text(
        'Предоставьте номер \n Вы можете отправить его с помощью кнопки ниже или ввести вручную в формате +79123456789.',
        reply_markup=ReplyKeyboardMarkup(
            [[{"text": "Отправить номер телефона", "request_contact": True}],
             ['Назад']],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    else:
        await update.message.reply_text(
        'Provide the number \n You can send it using the button below or enter it manually in the format +79123456789.',
        reply_markup=ReplyKeyboardMarkup(
            [[{"text": "Send phone number", "request_contact": True}],
             ['Back']],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )    

    return FIO

async def Get_FIO(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    user = update.message.from_user
    language = context.user_data.get('language', 'English')
    lecture = context.user_data.get('Lecture', 'feedback')

    context.user_data['Number'] = update.message.contact.phone_number if update.message.contact else update.message.text

    if context.user_data.get('Number', 'Back') in ['Назад', 'Back']:
        if language == 'Russian':
            await update.message.reply_text(
                f"Вы выбрали \n {lecture}. \n Введите ФИО",
                reply_markup=ReplyKeyboardMarkup(
                    [['Назад']]
                ),
            )
            return REGISTRATION
        
        elif language == 'English':
            await update.message.reply_text(
                f"You selected \n {lecture}. \n Text your Name",
                reply_markup=ReplyKeyboardMarkup(
                    [['Back']]
                ),
            )
            return REGISTRATION

    if language == 'Russian':
        await update.message.reply_text(
            "Напишите сообщение в свободной форме",
            reply_markup=ReplyKeyboardMarkup(
                [['Назад']]
            ),
        )
    else:
        await update.message.reply_text(
            "Write a message in free form",
            reply_markup=ReplyKeyboardMarkup(
                [['Back']]
            ),
        )
    return FEEDBACK

async def day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    day = update.message.text
    language = context.user_data.get('language', 'English')
    Sport = context.user_data.get('Sport', 'Skateboarding')
    event = context.user_data.get('event','schedule')

    if day in ['НАЗАД', 'BACK']:
        if language == 'Russian':
            await update.message.reply_text(
                'Меню',
                reply_markup=ru_menu_markup,
            )
        else:
            await update.message.reply_text(
                'Menu',
                reply_markup=en_menu_markup,
            )
        return SELECTING_MENU
    
    if event == 'photos':
        day = day.split('.')
        day = f'2025-{day[1]}-{day[0]}'

        #фотоотчет
        with open('contests.json', 'r', encoding='UTF-8') as file:
            links = json.load(file)
        
        for items in links:
            if items[Sport] != ',' and items['date'] == day:
                links = items[Sport].split(',')
                break

        keyboard = [
            [
                InlineKeyboardButton("VK", url=links[0]),
                InlineKeyboardButton("Yandex", url=links[1][1:]),
                ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if language == 'Russian':
            await update.message.reply_text('Выберите альбом', reply_markup=reply_markup)
        else:
            await update.message.reply_text('Choose album', reply_markup=reply_markup)

        if language == 'Russian':
            await update.message.reply_text(
                "Меню",
                reply_markup=ru_menu_markup,
            )
        else:
            await update.message.reply_text(
                "Menu",
                reply_markup=en_menu_markup,
            )
        return SELECTING_MENU
        
    day = day.split('.')
    day = f'2025-{day[1]}-{day[0]}.txt'

    for filename in os.listdir(f'{language}/{Sport}'):
        print(filename, ' ', day)
        if filename == day:
            with open(f"{language}/{Sport}/{filename}", 'r', encoding='utf-8') as file:
                text = file.read()
            break
        
    if language == 'Russian':
        await update.message.reply_text(
            text,
            reply_markup=ru_menu_markup,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=en_menu_markup,
            parse_mode="HTML",
        )
    return SELECTING_MENU


async def menu_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    menu = update.message.text
    language = context.user_data.get('language', 'English')
    Sport = context.user_data.get('Sport', 'Skateboardig')

    if menu in ['Полное расписание','Full schedule']:
        context.user_data['event'] = 'schedule'
        
        if language == 'Russian':
            master_keybord = [['НАЗАД']]
        else:
            master_keybord = [['BACK']]
            
        
        files = os.listdir(f'{language}/{Sport}')
        files_sorted = sorted(files, key=lambda x: tuple(map(int, x.split('.')[0].split('-'))))

        for filename in files_sorted:
            a = []
            filename = filename.split('.')
            title = filename[0].split('-')
            title = f'{title[2]}.{title[1]}'
            a.append(title)
            master_keybord.append(a)
        
        master_markup = ReplyKeyboardMarkup(master_keybord, one_time_keyboard=True)

        if language == 'Russian':
            await update.message.reply_text(
                    'Выберите день',
                    reply_markup=master_markup,
                )
        else:   
            await update.message.reply_text(
                    'Select day',
                    reply_markup=master_markup,
                )

        return SELECTING_DAY
    if menu in ['Расписание на завтра','Tomorrow`s schedule']:

        full_schedule = ''

        for filename in os.listdir(f'{language}/{Sport}'):
            target_date = filename.split('.')[0]
            print(target_date, '   ', date.today() + timedelta(days=1))
            if target_date == str(date.today() + timedelta(days=1)):
                with open(f'{language}/{Sport}/{filename}', 'r', encoding='utf-8') as file:
                    full_schedule = file.read()
                break
            
        
        if full_schedule == '':
            if language == 'Russian':
                full_schedule = 'Мероприятий не запланировано'
            else:
                full_schedule = 'There are no events planned'

        if language == 'Russian':
            await update.message.reply_text(
                f"{full_schedule}",
                reply_markup=ru_menu_markup,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"{full_schedule}",
                reply_markup=en_menu_markup,
                parse_mode="HTML"
            )
        return SELECTING_MENU

    if menu in ['Фотоотчет','Photos']:

        context.user_data['event'] = 'photos'

        if language == 'Russian':
            master_keybord = [['НАЗАД']]
        else:
            master_keybord = [['BACK']]

        with open(f"contests.json", 'r', encoding='utf-8') as file:
                contests = json.load(file)
        
        for items in contests:
            a = []
            if items[Sport] != ',':
                title = items['date'].split('-')
                title = f'{title[2]}.{title[1]}'
                a.append(title)
                master_keybord.append(a)
        
        master_markup = ReplyKeyboardMarkup(master_keybord, one_time_keyboard=True)

        if language == 'Russian':
            await update.message.reply_text(
                    'Выберите день',
                    reply_markup=master_markup,
                )
        else:   
            await update.message.reply_text(
                    'Select day',
                    reply_markup=master_markup,
                )

        return SELECTING_DAY

    if menu in ['Настройки','Settings']:
        await update.message.reply_text(
            "Пожалуйста, выберите язык / Please select your language:",
            reply_markup=language_markup,
        )
        return SELECTING_LANGUAGE
    
    if menu in ['Главное меню','Main menu']:

        if language == "Russian":
            await update.message.reply_text(
                f"Выберите вид спорта",
                reply_markup=ru_sport_markup,
                
            )
        elif language == "English":
            await update.message.reply_text(
                f"Select a sport",
                reply_markup=en_sport_markup,

            )
        return SELECTING_SPORT
    
    if menu in ['Обратная связь','Feedback']:
        
        if language == 'Russian':
            await update.message.reply_text(
                f"Введите ФИО",
                reply_markup=ReplyKeyboardMarkup(
                        [['Назад']]
                    ),
            )
            return REGISTRATION
        
        elif language == 'English':
            await update.message.reply_text(
                f"Text your Name",
                reply_markup=ReplyKeyboardMarkup(
                        [['Back']]
                    ),
            )
            return REGISTRATION
    
    if menu.lower() == 'рассылка всем':
        context.user_data['event'] = menu.lower()
        if user.id not in ADMIN_IDS:
            await update.message.reply_text(
            f"У вас нет доступа к этой комманде",
                reply_markup=ru_menu_markup
            )
            return SELECTING_MENU

        await update.message.reply_text(
            "Введите сообщение для рассылки (можно с медиа):",
            reply_markup=ReplyKeyboardMarkup([["Отменить"]], one_time_keyboard=True)
        )
        return BROADCAST_MESSAGE
    
    if menu.lower() == 'рассылка по спорту':

        context.user_data['event'] = menu.lower()

        if user.id not in ADMIN_IDS:
            await update.message.reply_text(
            f"У вас нет доступа к этой комманде",
                reply_markup=ru_menu_markup
            )
            return SELECTING_MENU

        await update.message.reply_text(
            "Введите сообщение для рассылки (можно с медиа):",
            reply_markup=ReplyKeyboardMarkup([["Отменить"]], one_time_keyboard=True)
        )
        return BROADCAST_MESSAGE


async def sport_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    Sport = update.message.text
    language = context.user_data.get('language', 'English')

    # Сохраняем язык в контексте пользователя

    if Sport in ['Настройки','Settings']:
        await update.message.reply_text(
            "Пожалуйста, выберите язык / Please select your language:",
            reply_markup=language_markup,
        )
        return SELECTING_LANGUAGE
    else:

        if language == 'Russian':

            await update.message.reply_text(
                f"Вы выбрали {Sport}. ",
                reply_markup=ru_menu_markup,
            )
            Sport = Sport_bef[Sports_ru.index(Sport)]
            context.user_data['Sport'] = Sport
        elif language == 'English':
            context.user_data['Sport'] = Sport
            await update.message.reply_text(
                f"You selected {Sport}. ",
                reply_markup=en_menu_markup,
            )
            Sport = Sport_bef[Sports_en.index(Sport)]
            context.user_data['Sport'] = Sport
        user_data = get_user_data(user.id)
        user_data.update({
            'user_id': user.id,
            'sport': Sport
        })
        
        # Сохраняем обновленные данные
        save_user_data(user_data)
        
        return SELECTING_MENU

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    language = update.message.text

    Sport = context.user_data.get('Sport', 'NN')

    if language == 'Русский':
        language = 'Russian'
    
    # Сохраняем язык в контексте пользователя
    context.user_data['language'] = language

    if Sport != 'NN':

        if language == 'Russian':
            await update.message.reply_text(
                f"Язык {language}",
                reply_markup=ru_menu_markup,
            )
            return SELECTING_MENU
        elif language == 'English':
            await update.message.reply_text(
                f"Language {language}",
                reply_markup=en_menu_markup,
            )
            return SELECTING_MENU
    
    if language == "Russian":
        await update.message.reply_text(
            f"Вы выбрали русский язык. Чем могу помочь?",
            reply_markup=ru_sport_markup,
            
        )
        return SELECTING_SPORT
    elif language == "English":
        await update.message.reply_text(
            f"You selected English. How can I help you?",
            reply_markup=en_sport_markup,

        )
        return SELECTING_SPORT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Действие отменено / Action canceled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    # Создаем Application и передаем токен вашего бота
    application = Application.builder().token("BOT TOKEN").build()

    # Создаем обработчик разговоров
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_LANGUAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, language_selected)
            ],
            CHECKING_SUBSCRIPTION: [
                CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"),
            ],
            SELECTING_SPORT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sport_selected)
            ],
            SELECTING_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_selected)
            ],
            REGISTRATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, Get_registration)
            ],
            FIO: [
                MessageHandler(filters.CONTACT, Get_FIO),
                MessageHandler(filters.TEXT & ~filters.COMMAND, Get_FIO)
            ],
            SELECTING_DAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, day_selected)
            ],
            FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback)
            ],
            BROADCAST_MESSAGE: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.Document.ALL, 
                    broadcast_message
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()