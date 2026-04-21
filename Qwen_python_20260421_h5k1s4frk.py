import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# 🔑 Вставьте сюда токен от @BotFather
BOT_TOKEN = "8619542232:AAHHJfq7SYqBGdhkC16YB01xabmUYEiF9yc"

# 📦 Простое хранилище в памяти (для демонстрации)
# Структура: {user_id: [{"name": str, "deadline": datetime, "notified": bool}]}
tasks = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я персональный ассистент задач.\n\n"
        "📝 *Добавить задачу:* `/add 2024-12-31 15:00 Сдать отчёт`\n"
        "📋 *Список задач:* `/list`\n"
        "⏰ Я напомню за 1 час до дедлайна.",
        parse_mode="Markdown"
    )

@dp.message(Command("add"))
async def cmd_add(message: Message):
    # Ожидаем формат: /add YYYY-MM-DD HH:MM Название задачи
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("❌ Неверный формат.\nПример: `/add 2024-12-31 15:00 Сдать отчёт`", parse_mode="Markdown")
        return

    date_str, time_str, task_name = parts[1], parts[2], parts[3]

    try:
        deadline = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат даты/времени. Используйте `YYYY-MM-DD HH:MM`")
        return

    if deadline <= datetime.now():
        await message.answer("❌ Дедлайн должен быть в будущем.")
        return

    user_id = message.from_user.id
    if user_id not in tasks:
        tasks[user_id] = []
    tasks[user_id].append({"name": task_name, "deadline": deadline, "notified": False})

    await message.answer(
        f"✅ Задача добавлена:\n📌 *{task_name}*\n⏰ {deadline.strftime('%d.%m.%Y %H:%M')}",
        parse_mode="Markdown"
    )

@dp.message(Command("list"))
async def cmd_list(message: Message):
    user_id = message.from_user.id
    user_tasks = tasks.get(user_id, [])
    if not user_tasks:
        await message.answer("📭 У вас пока нет задач.")
        return

    response = "📋 *Ваши задачи:*\n"
    for i, t in enumerate(user_tasks, 1):
        status = "✅ Просрочено/выполнено" if t["deadline"] <= datetime.now() else f"⏳ до {t['deadline'].strftime('%d.%m %H:%M')}"
        response += f"{i}. *{t['name']}* — {status}\n"
    await message.answer(response, parse_mode="Markdown")

async def scheduler():
    """Фоновая проверка дедлайнов каждую минуту"""
    while True:
        now = datetime.now()
        for user_id in list(tasks.keys()):
            for task in tasks[user_id]:
                # Если задача ещё не просрочена и уведомление не отправлено
                if not task["notified"] and task["deadline"] > now:
                    time_left = task["deadline"] - now
                    # Уведомляем, когда осталось ≤ 1 часа
                    if time_left <= timedelta(hours=1):
                        minutes = int(time_left.total_seconds() // 60)
                        await bot.send_message(
                            user_id,
                            f"⏰ *Напоминание:* через {minutes} мин. {task['name']}",
                            parse_mode="Markdown"
                        )
                        task["notified"] = True
        await asyncio.sleep(60)  # Проверка каждую минуту

async def main():
    # Запускаем планировщик в фоне
    asyncio.create_task(scheduler())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())