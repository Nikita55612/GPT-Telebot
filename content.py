from telebot.types import InlineKeyboardMarkup as tbMarkup, InlineKeyboardButton as tbButton, BotCommand

#  Кнопки в меню бота
MY_COMMANDS = [BotCommand("client", "🔐 Личный кабинет"),
               BotCommand("create_image", "🖼 Генерация изображения"),
               BotCommand("clear_context", "🧹 Очистить контекст")]

#  бот поддержки
SUPPORT_BOT = "https://t.me/GPT_LiveSupport202X_bot"

TELEGRAM_CHANNEL = "https://t.me/Chat_Gpt_Free_Telegram_Bot_4"

#  Документация консоли
CMD_DOC = "Переменные окружения:\n/cmd dir()\n" \
          "Отправить сообщение всем пользователям:\n/cmd send_oll('Сообщение для всех пользователей', " \
          "'Ссылка на картинку. Не обязательно')\n" \
          "Отправить сообщение одному пользователю:\n/cmd send(id, 'Сообщение')\n" \
          "Заблокировать пользователя:\n/cmd ban(id)\n" \
          "Разблокировать пользователя:\n/cmd unban(id)\n" \
          "Получить параметры пользователя:\n/cmd get_user(id)\n" \
          "Изменить параметр пользователя:\n/cmd set_user(id, 'параметр', значение)\n" \
          "Получить историю пользователя:\n/cmd get_user_history(id)\n" \
          "Получить id всех пользователей:\n/cmd get_oll_users_id()\n" \
          "Добавить роль:\n/cmd add_role('название роли', 'promt')\n" \
          "Удалить роль:\n/cmd dell_role('название роли')\n" \
          "Просмотр ролей:\n/cmd get_roles()\n"

#  Стартовое сообщение
START_MESSAGE = "START_MESSAGE"

#  Информация о боте
BOT_INFO = f"BOT_INFO"

#  Информация о реферальной системе
REF_INFO = "REF_INFO"

#  Информация о ролях
ROLE_INFO = "Роль - это инструкция нейронной сети, она кардинально меняет поведение бота. При выборе роли " \
            "отличной от «Стандартная» бот может вести себя не предсказуемо. Будьте готовы, что нейросеть может " \
            "вас оскорбить или ввести в заблуждение. Параметр temperature влияет на контрастность выбранной роли."

#  Информация о контексте
CONTEXT_INFO = "Контекст нужен для того, чтобы нейронная сеть понимала общую суть диалога из предыдущих сообщений." \
               " Сохраненный контекст тратит токены. Контекст можно очистить если он больше не имеет " \
               "отношение к диалогу. Очистить контекст можно командой /clear_context или в личном кабинете " \
               "/client > «📝 Контекст» > «🧹 Очистить контекст»."

#  Информация о буфере контекста
CONTEXT_BUFFER_INFO = "Максимальный буфер контекста это лимит после которого не будет добавляться новый контекст." \
                      "По достижении лимита новый контекст будет заменять собой старый. Контекст можно вовсе " \
                      "отключить выставив буфер контекста в 0."

#  Информация об оплате
PAYMENT_INFO = "PAYMENT_INFO"

#  Информация об пополнении баланса
TOP_UP_BALANCE_INFO = "Сумму для пополнения можно указать самостоятельно, используя команду /pay.\n" \
                      "Пример: /pay 133.55"

#  Информация о настройках
SETTINGS_INFO = "SETTINGS_INFO"

#  Информация о том ка сделать запрос
REQUEST_INFO = "Доступные виды запроса: в чат, текстом с картинки, голосовым сообщением"

#  Поддержка
SUPPORT_INFO = "SUPPORT_INFO"

#  Информация о выводе средств
WITHDRAWAL_OF_FUNDS_INFO = "WITHDRAWAL_OF_FUNDS_INFO"

#  Информация о температуре
TEMPERATURE_INFO = "temperature — это гиперпараметр, используемый в некоторых моделях обработки естественного " \
                   "языка, включая ChatGPT, для управления уровнем случайности или «креативности» в " \
                   "сгенерированном тексте. Более высокие температуры приводят к более разнообразной и " \
                   "непредсказуемой производительности. И наоборот, более низкие температуры приводят к " \
                   "более консервативной и предсказуемой производительности."

#  Кнопки пополнения баланса. ("название кнопки": цена)
PAYMENTS_BUTTONS = {"99": 99.99, "199": 199.99, "499": 499.99, "999": 999.99, "1999": 1999.99, "4999": 4999.99, }

#  Кнопки стартового сообщения
START_MESSAGE_MARKUP = tbMarkup().add(
    tbButton("📥 Моя реферальная ссылка", callback_data="ref_url"),
    tbButton("🔐 Личный кабинет", callback_data="client"),
    tbButton("🌐 Подписаться на канал", url=TELEGRAM_CHANNEL),
    tbButton("🔄 Проверить подписку", callback_data="check_channel_sub"), row_width=2)

#  Кнопки личного кабинета
CLIENT_MARKUP = tbMarkup().add(
            tbButton("📊 Статистика", callback_data=f"statistics"),
            tbButton("⚙️ Настройки", callback_data="settings"),
            tbButton("📝 Контекст", callback_data="context"),
            tbButton("❓ О боте", callback_data="bot_info"), row_width=2).add(
            tbButton("💎 Оплата", callback_data="payment"), row_width=1)

#  Кнопки инф. о боте
BOT_INFO_MARKUP = tbMarkup().add(
    tbButton("О реферальной системе", callback_data="ref_info"),
    tbButton("Как сделать запрос", callback_data="request_info"),
    tbButton("О настройках", callback_data="settings_info"),
    tbButton("Поддержка", callback_data="support_info"), row_width=2).add(
    tbButton("⬅️ Назад", callback_data="client"), row_width=1)

#  Кнопки контекста
CONTEXT_MARKUP = tbMarkup().add(
    tbButton("🧹 Очистить контекст", callback_data="clear_context"),
    tbButton("🔂 Макс. буфер контекста", callback_data="context_buffer"),
    tbButton("⬅️ Назад", callback_data="client"), row_width=2)

#  Кнопки оплаты
PAYMENT_MARKUP = tbMarkup().add(
    tbButton("💰 Пополнить баланс", callback_data="top_up_balance"),
    tbButton("🛒 Купить токены", callback_data="buy_tokens"),
    tbButton("📤 Вывод средств", callback_data="withdrawal_of_funds"),
    tbButton("⬅️ Назад", callback_data="client"), row_width=1)

#  Кнопки покупки токенов
BUY_TOKENS_MARKUP = tbMarkup().add(
    tbButton("10.000", callback_data="buy_tokens=10000"),
    tbButton("20.000", callback_data="buy_tokens=20000"),
    tbButton("50.000", callback_data="buy_tokens=50000"),
    tbButton("100.000", callback_data="buy_tokens=100000"), row_width=1).add(
    tbButton("⬅️ Назад", callback_data="payment"),
    tbButton("🔄 Обновить", callback_data="buy_tokens"), row_width=2)

ADMIN_PANEL_MARKUP = tbMarkup().add(
    tbButton("📄 Документация консоли", callback_data="admin_panel_doc"), row_width=1).add(
    tbButton("📥 История", callback_data="get_users_history"),
    tbButton("📥 Профайлы", callback_data="get_user_profiles"),
    tbButton("📥 Логи", callback_data="get_logs"),
    tbButton("🗑 Очистить логи", callback_data="clear_logs"),
    tbButton("❌ Закрыть", callback_data="close"),
    tbButton("🔄 Обновить", callback_data="admin_panel"), row_width=2)

#  Кнопки реферальной системы
REF_INFO_MARKUP = tbMarkup().add(
    tbButton("📥 Моя реферальная ссылка", callback_data="ref_url"),
    tbButton("⬅️ Назад", callback_data="bot_info"), row_width=1)

#  Кнопки в статистике
STATISTICS_MARKUP = tbMarkup().add(
    tbButton("📈 График расхода токенов", callback_data="plt_total_tokens")).add(
    tbButton("⬅️ Назад", callback_data="statistics_back_client"))

CHANNEL_SUBSCRIPTION_MARKUP = tbMarkup().add(
    tbButton("🌐 Перейти на канал", url=TELEGRAM_CHANNEL))

WITHDRAWAL_OF_FUNDS_MARKUP = tbMarkup().add(
    tbButton("📩 Отправить заявку", url=SUPPORT_BOT),
    tbButton("⬅️ Назад", callback_data="payment"), row_width=1)

INSUFFICIENT_FUNDS_MARKUP = tbMarkup().add(
    tbButton("💰 Пополнить баланс", callback_data="top_up_balance"),
    tbButton("❌ Закрыть", callback_data="close"), row_width=1)

STAT_BACK_CLIENT_MARKUP = tbMarkup().add(
    tbButton("⬅️ Назад", callback_data="statistics_back_client"))

TO_BOT_INFO_MARKUP = tbMarkup().add(tbButton("⬅️ Назад", callback_data="bot_info"))

SUPPORT_INFO_MARKUP = tbMarkup().add(
    tbButton("📨 Написать", url=SUPPORT_BOT),
    tbButton("⬅️ Назад", callback_data="bot_info"), row_width=1)

VOICE_TO_TEXT_MARKUP = tbMarkup().add(
    tbButton("Показать текст", callback_data="voice_to_text"))

REMAKE_IMAGE_MARKUP = tbMarkup().add(
    tbButton("🔄  Переделать изображение", callback_data="remake_image"))

CLOSE_MARKUP = tbMarkup().add(
    tbButton("❌ Закрыть", callback_data="close"))
