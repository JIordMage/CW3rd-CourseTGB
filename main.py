import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

from author import TKN, usrnme, psswrd

# from selenium.webdriver.common.action_chains import ActionChains


# путь к  ChromeDriver
driver_path = r'C:\Users\Даниил-ПК\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'

# Создание экземпляра веб-драйвера
driver = webdriver.Chrome(executable_path=driver_path)

# URL страницы Pinterest для входа
login_url = 'https://www.pinterest.com/login/'

# Открытие страницы веб-драйвером
driver.get(login_url)

# Задержка для загрузки страницы (может потребоваться настроить в зависимости от скорости интернета)
time.sleep(5)

# учетные данные
username = usrnme
password = psswrd

# Нахождение полей ввода логина и пароля
username_input = driver.find_element('name', 'id')
password_input = driver.find_element('name', 'password')

# Ввод логина и пароля
username_input.send_keys(username)
password_input.send_keys(password)

# Нажатие клавиши Enter для входа
password_input.send_keys(Keys.RETURN)

# Задержка для завершения входа (может потребоваться настроить в зависимости от скорости интернета)
time.sleep(5)

# Теперь у вас есть открытая сессия с авторизованным пользователем веб-браузера


# токен от BotFather
TOKEN = TKN
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(func=lambda message: True, content_types=['new_chat_members'])
def new_chat_member(message):
    bot.send_message(message.chat.id, "Привет! Я бот для получения фотографий из Pinterest. "
                                      "Используйте команду /get_pins {никнейм} [число пинов] для получения фотографий.")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton('/start')

    # Добавляем кнопки на клавиатуру
    markup.add(start_button)

    # Ваше приветственное сообщение
    welcome_message = "Привет! Этот бот может получить фотографии из Pinterest. " \
                      "Используйте команду /get_pins {никнейм} [число пинов] для получения фотографий."

    # Отправляем приветственное сообщение с клавиатурой
    bot.reply_to(message, welcome_message, reply_markup=markup)


# Глобальные переменные для хранения состояния
last_username = None
last_photo_index = None
current_photo_index = 0


@bot.message_handler(commands=['get_pins'])
def get_pins(message):
    global last_username, last_photo_index, current_photo_index
    try:
        # Разбираем команду пользователя
        command_parts = message.text.split()
# сделать проверку команды
        if (len(command_parts) > 2 and command_parts[2].isdigit()) or len(command_parts) == 2:

            if len(command_parts) > 2:
                photo_count = int(command_parts[2])

            # Извлекаем никнейм
            user_name = command_parts[1]
            url = f"https://ru.pinterest.com/{user_name}/pins/"
            driver.get(url)
            response = requests.get(url)
            if response.status_code == 200:

                bot.reply_to(message, "Происходит загрузка фотографий!")
                driver.implicitly_wait(15)
                time.sleep(2.5)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                images = soup.find_all('a', class_="Wk9 xQ4 CCY S9z DUt iyn kVc agv LIa")

                if images:

                    # Извлекаем число фотографий, если указано
                    photo_count = int(command_parts[2]) if len(command_parts) > 2 else 1
                    for _ in range(photo_count):
                        # Проверяем, если текущий пользователь не совпадает с предыдущим (переместить!)
                        if last_username != user_name:
                            last_username = user_name
                            last_photo_index = None
                            current_photo_index = 0
                        time.sleep(1.5)
                        for _ in range(current_photo_index // 5):

                            body = driver.find_element("tag name", "body")

                            body.send_keys(Keys.PAGE_DOWN)
                            time.sleep(0.125)

                        time.sleep(1.5)
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        images = soup.find_all('a', class_="Wk9 xQ4 CCY S9z DUt iyn kVc agv LIa")
                        # Проверяем, если есть еще фотографии для загрузки
                        if current_photo_index < len(images):
                            photo_url = images[current_photo_index]['href']
                            driver.get(f"https://ru.pinterest.com{photo_url}")
                            driver.implicitly_wait(10)

                            body = driver.find_element("tag name", "body")
                            body.send_keys(Keys.PAGE_DOWN)
                            body.send_keys(Keys.PAGE_DOWN)

                            time.sleep(1)
                            # Получаем исходный код страницы после перехода
                            current_page_source = driver.page_source

                            # Создаем новый объект BeautifulSoup для новой страницы
                            current_soup = BeautifulSoup(current_page_source, 'html.parser')

                            # Находим все теги img для изображений
                            imgs = current_soup.find_all('img', class_="hCL kVc L4E MIw")
                            if imgs:
                                # Получаем ссылку на изображение
                                img_src = imgs[1]['src']
    # в теории можно перемещаться к последнему сохраненному src, обновлять поиск
    # и продолжать сбор изображений, но новый поиск должен обязательно начинаться с следующего изображения
    # что вызывает некоторые изъяны

                                # Отправляем сообщение с изображением
                                bot.send_photo(message.chat.id, photo=img_src,
                                               caption=f"Изображение {current_photo_index + 1}")
                            current_photo_index += 1

                            driver.back()

                        else:
                            bot.reply_to(message, f"Количество запрошенных фотографий превышает количество доступных "
                                                  f"боту. Попробуйте использовать команду еще раз.")
                            break
                else:
                    bot.reply_to(message, "К сожалению, фотографии не найдены.")
            else:
                bot.reply_to(message, f"Ошибка при запросе к Pinterest. Код статуса: {response.status_code}")
        else:
            bot.reply_to(message, f"Число пинов должно быть положительным целым числом больше нуля")
    except IndexError:
        bot.reply_to(message, "Используйте команду /get_pins {никнейм} [число пинов]")


if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    finally:
        driver.quit()
