
# Ключи (str) #

# Основной телеграмм бот
MAIN_TELEGRAM_API_KEY = ""
# Тестовый телеграмм бот
TEST_TELEGRAM_API_KEY = ""
# !!!Присвоение бота (str or TELEGRAM_KEY obj)
TELEGRAM_API_KEY = TEST_TELEGRAM_API_KEY
# ID телеграмм канала, в котором будет проверяться подписка
CHANNEL_TELEGRAM_ID = "@Chat_Gpt_Free_Telegram_Bot_4"
# Токен YOOMONEY (str)
YOOMONEY_TOKEN = ""

# стоимость картинки в токенах (int)
TOKENS_PER_PICTURE = 2500
# множитель курса токена (float)
TOKEN_RATE_MULTIPLIER = 1.0
# награда за подписку на канал (баланс в рублях) (int or float)
SUBSCRIPTION_REWARD = 10

# Настройка начального профайла пользователя #

# начальный процент от реферала 1 ур. %(int or float)
START_USER_REF_PERCENT = 10
# начальный процент от реферала 2 ур. %(int or float)
START_USER_SUB_REF_PERCENT = 5
# начальное количество токенов (int)
START_USER_TOKENS = 20000
# начальный лимит токенов (int)
START_USER_LIMIT_TOKENS = 20000
# дней до сброса лимита токенов (int)
DAYS_BEFORE_RESETTING_TOKENS = 7
# начальный максимальный размер буфера контекста (int)
START_USER_MAX_CONTEXT_SIZE = 1
# максимально возможный размер буфера контекста (int)
START_USER_MAX_CONTEXT_BUFFER = 2
# начальное ограничение на длину ответа в токенах (int)
START_USER_MAX_TOKENS = 1100
# начальная модель gpt/ str (gpt-3.5-turbo or gpt-4)
START_USER_MODEL = "gpt-3.5-turbo"
# начальное значение параметра температуры (float)
START_USER_TEMPERATURE = 0.1
# начальный статус пользователя (str)
START_USER_STATUS = "user"

# !ADVANCED! #

# главная директория данных пользователей (str)
USERS_DIR = "users_data"
# главная директория логов (str)
LOGS_DIR = "logs.log"
# главная директория ролей (str)
ROLES_DIR = "roles.json"
# главная ключей для api OPENAI (str)
OPENAI_KEYS_DIR = "openai_keys.json"
# сохранение резервной копии данных пользователей/ bool (True or False)
USERS_BACKUP = True
# максимальный размер кэша в байтах (int)
CACHE_MAX_SIZE = 207374182

# !CONSTANTS! #
TB_COMMANDS = ["start", "client", "create_image", "clear_context", "pay", "cmd", "a"]


