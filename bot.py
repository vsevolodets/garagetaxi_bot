import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import BaseFilter

API_TOKEN = '8681478738:AAFbHzckzVQdEqRdHsgmtqjwRoKnHTnaAlg'
BOSS_ID = 746633664  # Telegram ID шефа

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

boss_messages = {}


class BossFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == BOSS_ID


def get_mention(user):
    if isinstance(user, types.User):
        return user.first_name
    elif isinstance(user, str):
        return user
    return str(user)


@dp.message(BossFilter())
async def boss_message(message: Message):
    if not message.text:
        return

    if '?' not in message.text or len(message.text.strip()) < 5:
        return

    print(f"[LOG] Сообщение шефа: {message.text} ({message.message_id})")

    mentioned_user = None
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                mentioned_user = entity.user
                break
            elif entity.type == "mention":
                username = message.text[entity.offset: entity.offset + entity.length]
                mentioned_user = username
                break

    boss_messages[message.message_id] = {
        "chat_id": message.chat.id,
        "replied": False,
        "mentioned_user": mentioned_user,
        "bot_replies": [],
        "step": 0
    }

    asyncio.create_task(auto_reply_loop(message.message_id))


@dp.message()
async def any_reply(message: Message):
    if not message.reply_to_message:
        return

    replied_id = message.reply_to_message.message_id

    if replied_id not in boss_messages:
        return

    print(f"[LOG] Получен ответ на сообщение шефа: {message.text}")

    data = boss_messages[replied_id]
    data["replied"] = True

    for msg_id in data["bot_replies"]:
        try:
            await bot.delete_message(
                chat_id=data["chat_id"],
                message_id=msg_id
            )
        except Exception as e:
            print(f"[ERROR] Не удалось удалить сообщение: {e}")

    boss_messages.pop(replied_id, None)


async def auto_reply_loop(message_id):
    timings = [4 * 60, 4 * 60, 4 * 60, 60, 60, 60, 4 * 60]

    texts = [
        "Ответа не было",
        "Напоминаю, ответа не было",
        "Все ещё нет ответа",
        "Напоминаю ещё раз",
        "Напоминаю ещё раз",
        "Напоминаю ещё раз",
        "Штраф 5000 рублей"
    ]

    data = boss_messages.get(message_id)
    if not data:
        return

    for i, delay in enumerate(timings):
        await asyncio.sleep(delay)

        data = boss_messages.get(message_id)
        if not data or data["replied"]:
            break

        for msg_id in data["bot_replies"]:
            try:
                await bot.delete_message(
                    chat_id=data["chat_id"],
                    message_id=msg_id
                )
            except Exception as e:
                print(f"[ERROR] Не удалось удалить сообщение: {e}")

        data["bot_replies"].clear()

        text = texts[i]

        if data["mentioned_user"]:
            text += " " + get_mention(data["mentioned_user"])

        try:
            sent = await bot.send_message(
                chat_id=data["chat_id"],
                text=text,
                reply_to_message_id=message_id
            )

            data["bot_replies"].append(sent.message_id)
            data["step"] = i + 1

        except Exception as e:
            print(f"[ERROR] Ошибка отправки сообщения: {e}")

    boss_messages.pop(message_id, None)


async def main():
    print(f"[LOG] Бот запущен, токен: {API_TOKEN[:10]}...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
