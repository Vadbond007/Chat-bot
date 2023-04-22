import logging
import psycopg2
from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Инициализация логгера
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Подключение к базе данных Postgresql
conn = psycopg2.connect(
    host="localhost",
    database="TheVaper",
    user="postgres",
    password="28012003"
)

# Инициализация экземпляра Updater с помощью токена бота, полученного в шаге 1
updater = Updater(token='6292228126:AAGdDxDXs65BSsDEJjxQDIsJ5EbUaUT0crI', use_context=True)

# Создание меню с кнопками
def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🛒отложить"), KeyboardButton("🛍️товары")],
        [KeyboardButton("🎁акции"), KeyboardButton("💬помощь")],
        [KeyboardButton("👤кабинет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функция, создающая меню с кнопками товаров
def products_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🔋💨🚬Pod-системы"), KeyboardButton("🚮Одноразовые устройства")],
        [KeyboardButton("💧Жидкость"), KeyboardButton("💨Атомайзеры")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функция, которая будет вызываться при нажатии на кнопку "Товары"
def show_products_menu(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите категорию:", reply_markup=products_menu())

# Функция, которая будет вызываться при нажатии на одну из кнопок товаров
def show_products(update: Update, context: CallbackContext) -> None:
    # Получение текста сообщения с названием категории товаров
    product_category = update.message.text
    
    # Запрос в базу данных на поиск товаров по категории
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE category ILIKE %s", ('%' + product_category + '%',))
    products = cur.fetchall()
    conn.commit()
    
    # Если товары найдены
    if products:
        # Формирование сообщения со списком товаров
        response = f"Список товаров в категории \"{product_category}\":\n"
        for product in products:
            response += f"{product[1]} - Цена: {product[3]} руб.\n"
            response += f"  Цвет: {product[4]}, Вкус: {product[5]}, Крепкость: {product[6]}\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    else:
        # Отправка сообщения об отсутствии товаров
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"К сожалению, товары в категории \"{product_category}\" не найдены.")
        
# Регистрация обработчиков для кнопок "Товары" и категорий товаров
updater.dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(товары)$'), show_products_menu))
updater.dispatcher.add_handler(MessageHandler(Filters.text & (Filters.regex(r'^Pod-системы$') | Filters.regex(r'^Одноразовые устройства$') | Filters.regex(r'^Жидкость$') | Filters.regex(r'^Атомайзеры$')), show_products))


# Функция для вывода списка категорий товаров
def show_categories(update: Update, context: CallbackContext) -> None:
    # Создаем клавиатуру с категориями товаров
    categories_keyboard = [
        [KeyboardButton("Pod-системы"), KeyboardButton("одноразовые устройства")],
        [KeyboardButton("жидкость"), KeyboardButton("атомайзеры")],
        [KeyboardButton("назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(categories_keyboard, resize_keyboard=True)
    # Отправляем сообщение пользователю с клавиатурой категорий товаров
    update.message.reply_text("Выберите категорию товаров:", reply_markup=reply_markup)

# Функция для вывода списка товаров в выбранной категории
def show_products(update: Update, context: CallbackContext) -> None:
    # Получаем название категории товаров, выбранное пользователем
    category = update.message.text
    # Запрос в базу данных для получения списка товаров в выбранной категории
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products WHERE category = %s", (category,))
    products = cursor.fetchall()
    # Создаем клавиатуру с товарами
    products_keyboard = []
    for product in products:
        products_keyboard.append([KeyboardButton(product[0])])
    products_keyboard.append([KeyboardButton("назад")])
    reply_markup = ReplyKeyboardMarkup(products_keyboard, resize_keyboard=True)
    # Отправляем сообщение пользователю с клавиатурой товаров
    update.message.reply_text("Выберите товар:", reply_markup=reply_markup)
    # Сохраняем выбранную категорию товаров в контексте пользователя
    context.user_data["category"] = category

# Функция для вывода списка магазинов и отправки заказа в выбранный магазин
def show_stores_and_send_order(update: Update, context: CallbackContext) -> None:
    # Получаем название товара, выбранного пользователем
    product = update.message.text
    # Создаем клавиатуру с магазинами
    stores_keyboard = [
        [KeyboardButton("магазин 1"), KeyboardButton("магазин 2")],
        [KeyboardButton("магазин 3"), KeyboardButton("магазин 4")],
        [KeyboardButton("назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(stores_keyboard, resize_keyboard=True)
    # Отправляем сообщение пользователю с клавиатурой магазинов и просим ввести комментарий
    update.message.reply_text("Выберите магазин:", reply_markup=reply_markup)
    update.message.reply_text("Введите комментарий (пожелания):", reply_markup=ForceReply())
    # Сохраняем выбранный товар в контексте пользователя
    context.user_data["product"] = product

# Функция для отправки заказа в выбранный магазин
def send_order(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    db_cursor = conn.cursor()
    user_id = user.id
    comment = context.user_data.get('comment', None)
    order_items = context.user_data.get('order_items', [])
    store = context.user_data.get('store', None)

    # Проверяем, есть ли у пользователя отложенные товары
    if not order_items:
        context.bot.send_message(chat_id=chat_id, text='У вас нет отложенных товаров.')
        return

    # Проверяем, выбран ли магазин
    if not store:
        context.bot.send_message(chat_id=chat_id, text='Пожалуйста, выберите магазин.')
        return

    # Формируем текст сообщения для отправки сотруднику магазина
    order_text = f'Пользователь {user_id} заказал следующие товары:\n\n'
    for item in order_items:
        order_text += f'{item["name"]} - {item["price"]} руб.\n'
    order_text += f'\nКомментарий: {comment if comment else "нет"}'

    # Отправляем сообщение сотруднику магазина
    try:
        db_cursor.execute('INSERT INTO orders (store_id, user_id, order_text) VALUES (%s, %s, %s)',
                          (store, user_id, order_text))
        conn.commit()
        context.bot.send_message(chat_id=chat_id, text='Заказ отправлен в магазин.')
    except Exception as e:
        conn.rollback()
        context.bot.send_message(chat_id=chat_id, text=f'Ошибка при отправке заказа: {str(e)}')

# Функция-обработчик для кнопки "отложить"
def delay(update: Update, context: CallbackContext) -> None:
    # Создаем меню с категориями товаров
    categories_menu = [['Pod-системы', 'одноразовые устройства'], ['жидкость', 'атомайзеры']]
    categories_keyboard = ReplyKeyboardMarkup(categories_menu, one_time_keyboard=True, resize_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите категорию товаров:", reply_markup=categories_keyboard)
    return WAITING_CATEGORY

# Функция-обработчик для выбора категории товаров
def choose_category(update: Update, context: CallbackContext) -> None:
    # Получаем выбранную категорию товаров
    category = update.message.text

    # Формируем SQL-запрос для получения списка товаров из выбранной категории
    db_cursor = conn.cursor()
    db_cursor.execute('SELECT id, name, price FROM products WHERE category = %s', (category,))
    products = db_cursor.fetchall()

    # Создаем кнопки для каждого товара
    products_menu = [[KeyboardButton(product[1])] for product in products]
    products_menu.append([KeyboardButton('Готово')])
    products_keyboard = ReplyKeyboardMarkup(products_menu, one_time_keyboard=True, resize_keyboard=True)

    # Сохраняем выбранную категорию товаров в контексте пользователя
    context.user_data['category'] = category

    # Отправляем сообщение с выбором товаров
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Выберите товар из категории '{category}':", reply_markup=products_keyboard)




# Функция-обработчик для команды /start
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Привет👋, {user.first_name}! Я бот, давай пообщаемся.", reply_markup=main_menu())

def echo(update: Update, context: CallbackContext) -> None:
    # Получение текста сообщения
    text = update.message.text
    
    # Запись сообщения в базу данных
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
    conn.commit()
    
    # Поиск похожих наименований товаров в базе данных
    similar_products = search_similar_products(text, conn)
    
    # Отправка ответного сообщения
    if len(similar_products) > 0:
        response_text = "К сожалению, товар не найден. Возможно, вы имели в виду один из следующих товаров:\n\n"
        response_text += "\n".join(similar_products)
    else:
        response_text = text
        
    context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)
    

# Функция-обработчик для выбора товара и проверки наличия
def check_product(update: Update, context: CallbackContext) -> None:
    # Получение текста сообщения с названием товара
    product_name = update.message.text

    # Запрос в базу данных на поиск товара по названию
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE name ILIKE %s", ('%' + product_name + '%',))
    product = cur.fetchone()
    conn.commit()

    # Если товар найден
    if product:
        # Проверка наличия товара
        if product[2] > 0:
            # Отправка сообщения о наличии товара и его цене
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Товар \"{product[1]}\" в наличии. Цена: {product[3]} руб.")
        else:
            # Отправка сообщения об отсутствии товара
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"К сожалению, товар \"{product[1]}\" закончился. Выберите другой товар.")
    else:
        # Отправка сообщения об отсутствии товара
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"К сожалению, товар с названием \"{product_name}\" не найден. Попробуйте выбрать другой товар.")

# Регистрация обработчика команды на выбор товара и проверку наличия
updater.dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^(Выбрать товар)$'), check_product))

#добавления записи о заказе в базу данных:
def add_order(user_id, product_name, quantity, price, store_name, pickup_time):
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (user_id, product_name, quantity, price, store_name, pickup_time) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, product_name, quantity, price, store_name, pickup_time))
    conn.commit()

#отправка уведомления о заказе сотруднику магазина:
def notify_store():
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE pickup_time <= NOW()")
    orders = cur.fetchall()
    for order in orders:
        message = f"Пользователь {order[1]} заказал {order[3]} единиц товара {order[2]}. Он хочет забрать его в магазине {order[5]} в {order[6]}."
        # Отправка уведомления сотруднику магазина


# Функция-обработчик для команды /search
def search(update: Update, context: CallbackContext) -> None:
    # Получение ключевого слова от пользователя
    keyword = context.args[0]
    
    # Поиск товаров, содержащих ключевое слово
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE to_tsvector('russian', description) @@ plainto_tsquery('russian', %s) ORDER BY price", (keyword,))
    rows = cur.fetchall()
    
    # Формирование сообщения с результатами поиска
    if len(rows) > 0:
        message = "Результаты поиска:\n\n"
        for row in rows:
            message += f"{row[1]} ({row[2]} руб.)\n"
    else:
        message = "Ничего не найдено."
    
    # Отправка сообщения
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

# Регистрация обработчиков команд и сообщений
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('search', search))
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))



def search_similar_products(product_name, conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM products")
    rows = cur.fetchall()

    product_names = [row[0] for row in rows]
    similar_names = process.extract(product_name, product_names, limit=5, scorer=fuzz.token_set_ratio)
    return [name[0] for name in similar_names]

# использование функции search_similar_products
similar_products = search_similar_products("product_name", conn)


def echo(update: Update, context: CallbackContext, conn: psycopg2.extensions.connection) -> None:
    # Получение текста сообщения
    text = update.message.text
    
    # Запись сообщения в базу данных
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
    conn.commit()
    
    # Поиск похожих наименований товаров в базе данных
    similar_products = search_similar_products(text)
    
    # Отправка ответного сообщения
    if len(similar_products) > 0:
        response_text = "К сожалению, товар не найден. Возможно, вы имели в виду один из следующих товаров:\n\n"
        response_text += "\n".join(similar_products)
    else:
        response_text = text
        
    context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)


# Запуск бота
updater.start_polling()
updater.idle()

# Закрытие соединения с базой данных
conn.close()
