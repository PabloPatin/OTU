import pandas as pd
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram import F
import asyncio
import sqlalchemy
import os
from dotenv import load_dotenv

import parse_timetables
from db_manager import ScheduleLoader, Lesson
load_dotenv()


# ключ в .env
bot = Bot(token=os.getenv("TG_API_KEY"))
dp = Dispatcher()

# loader = ScheduleLoader(db_url='postgresql://postgres:root@localhost:7546/shedule')
loader = ScheduleLoader(db_url=os.getenv("DB_URL"))

# Функция для корректного форматирования расписания
def format_daily_schedule(schedule: list[Lesson]):
    print(schedule)
    formatted_schedule = []
    for lesson in schedule:
        formatted_schedule.append(f"\t{lesson.time}: {lesson.name}")
    return "\n".join(formatted_schedule)

def format_schedule(schedule: dict[str,list[Lesson]]):
    formatted_schedule = []
    for day, lesson in schedule.items():
        formatted_schedule.append(f"\n{day}:")
        formatted_schedule.append(format_daily_schedule(lesson))
    return "\n".join(formatted_schedule)

# Функция для извлечения расписания для конкретного дня
def extract_day_schedule(group_name, day):
    if not group_column:
        return f"Группа {group_name} не найдена в расписании."
    group_column = group_column[0]
    # Колонка с временем
    time_column = df.columns[1]
    # Словарь для хранения расписания на день
    day_schedule = {}
    for index, row in df.iterrows():
        current_day = row[df.columns[0]]
        time = row[time_column]
        subject = row[group_column]
        # Проверка на корректность дня и недели
        if isinstance(current_day, str) and current_day.strip() == day:
            print(f"Проверка предмета: {subject}, для дня: {day}, время: {time}")  # Отладка
            if isinstance(subject, str):
                if week_type == "odd":
                    # Для нечетной недели (I или I и II)
                    if "I" in subject:
                        print(f"Добавлено для нечетной недели: {subject}")  # Отладка
                        day_schedule[time] = subject
                elif week_type == "even":
                    # Для четной недели (II или I и II)
                    if "II" in subject:
                        print(f"Добавлено для четной недели: {subject}")  # Отладка
                        day_schedule[time] = subject

    return format_schedule(
        {day: day_schedule}) if day_schedule else f"Для {day} не найдено расписания на {week_type}-ю неделю."


# Функция для извлечения полного расписания для недели
def extract_week_schedule(group_name):
    group_schedule = loader.get_weekly_schedule(group_name)
    return format_schedule(group_schedule)


# Основные клавиши
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Выбери группу")]
    ],
    resize_keyboard=True
)

# Клавиатура для выбора группы
group_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="АГС-22-1"), KeyboardButton(text="АГС-22-2"), KeyboardButton(text="АГС-22-3")],
        [KeyboardButton(text="ГГ-22-1"), KeyboardButton(text="ГГ-22-2"), KeyboardButton(text="ГК-22")],
        [KeyboardButton(text="ГС-22-1"), KeyboardButton(text="ГС-22-2"), KeyboardButton(text="ИГ-22-1")],
        [KeyboardButton(text="ИГ-22-2"), KeyboardButton(text="ПГС-22"), KeyboardButton(text="СПС-22")],
        [KeyboardButton(text="ИАС-22-1"), KeyboardButton(text="ИАС-22-2"), KeyboardButton(text="ИТУ-22")],
        [KeyboardButton(text="МП-22"), KeyboardButton(text="МТ-22"), KeyboardButton(text="САМ-22")],
        [KeyboardButton(text="ЭГ-22-1"), KeyboardButton(text="ЭГ-22-2")]
    ],
    resize_keyboard=True
)

# Клавиатура для выбора недели
week_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Четная неделя"), KeyboardButton(text="Нечетная неделя")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)
# Клавиатура для дней недели и полного расписания
def day_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Понедельник"), KeyboardButton(text="Вторник")],
            [KeyboardButton(text="Среда"), KeyboardButton(text="Четверг")],
            [KeyboardButton(text="Пятница")],
            [KeyboardButton(text="Показать всю неделю"), KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )


# Глобальные переменные для хранения выбранной группы и текущего шага
selected_group = ""
current_step = ""
week_type = ""
df = None  # Для хранения данных Excel


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    global current_step
    current_step = "start"
    await message.answer("Привет! Нажми 'Выбери группу', чтобы продолжить:", reply_markup=start_keyboard)


# Обработчик нажатия на кнопку "Выбери группу"
@dp.message(F.text == "Выбери группу")
async def choose_group(message: Message):
    global current_step, previous_step
    previous_step = current_step
    current_step = "group_selection"
    await message.answer("Выбери свою группу:", reply_markup=group_keyboard)


# Универсальный обработчик для всех групп
@dp.message(F.text.in_([
    "АГС-22-1", "АГС-22-2", "АГС-22-3",
    "ГГ-22-1", "ГГ-22-2", "ГК-22",
    "ГС-22-1", "ГС-22-2", "ИГ-22-1",
    "ИГ-22-2", "ПГС-22", "СПС-22",
    "ИАС-22-1", "ИАС-22-2", "ИТУ-22",
    "МП-22", "МТ-22", "САМ-22", "ЭГ-22-1", "ЭГ-22-2"
]))
async def handle_group_selection(message: Message):
    global selected_group, current_step, previous_step
    previous_step = current_step
    selected_group = message.text  # Сохраняем выбранную группу
    current_step = "week_selection"  # Переход на выбор недели
    await message.answer(f"Ты выбрал {selected_group}. Теперь выбери тип недели:", reply_markup=week_type_keyboard)


# Обработчик нажатия на неделю
@dp.message(F.text.in_(["Четная неделя", "Нечетная неделя"]))
async def handle_week_type(message: Message):
    global selected_group, current_step, previous_step, week_type
    previous_step = current_step
    week_type = "even" if message.text == "Четная неделя" else "odd"
    current_step = "day_selection"

    # Показываем кнопки для дней недели
    await message.answer(f"Выбрана {message.text}. Выберите день или просмотрите всю неделю:",
                         reply_markup=day_keyboard())


# Обработчик для выбора дня недели или полного расписания
@dp.message(F.text.in_(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]))
async def handle_day_selection(message: Message):
    global selected_group
    day = message.text
    lessons = loader.get_daily_schedule(selected_group, day)
    schedule = format_daily_schedule(lessons)
    await message.answer(schedule)


# Обработчик для показа полного расписания
@dp.message(F.text == "Показать всю неделю")
async def handle_full_week(message: Message):
    global selected_group
    # Показать расписание на всю неделю
    full_schedule = extract_week_schedule(selected_group)
    await message.answer(full_schedule)

# Обработчик кнопки "Назад" для возврата на предыдущие шаги
@dp.message(F.text == "Назад")
async def go_back(message: Message):
    global current_step, previous_step
    # Переходим на предыдущий шаг
    if current_step == "day_selection":
        current_step = "week_selection"
        await message.answer("Выбери тип недели:", reply_markup=week_type_keyboard)
    elif current_step == "week_selection":
        current_step = "group_selection"
        await message.answer("Выбери свою группу:", reply_markup=group_keyboard)
    elif current_step == "group_selection":
        current_step = "start"
        await message.answer("Привет! Нажми 'Выбери группу', чтобы продолжить:", reply_markup=start_keyboard)

        # Запуск бота
async def main():
    # Загружаем данные расписания при старте/парсим

    # parse_timetables.parse_timetables("timetables")

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())