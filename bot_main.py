import os
import asyncio
import aiohttp
import aiosqlite
from bs4 import BeautifulSoup
from aiogram import Bot
from dotenv import load_dotenv


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)


async def init_db():
    async with aiosqlite.connect("news.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sent_news (
                url TEXT PRIMARY KEY
            )
        """)
        await db.commit()


async def parse_and_send():
    url = "https://news.ycombinator.com/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_text = await response.text()

    soup = BeautifulSoup(html_text, "lxml")
    headlines = soup.select(".titleline > a")

    print("Парсинг завершён. Отправляю новости в Telegram...")

    async with aiosqlite.connect("news.db") as db:
        for line in headlines[:10]:
            news_url = line["href"]

            async with db.execute("SELECT 1 FROM sent_news WHERE url = ?", (news_url,)) as cursor:
                already_sent = await cursor.fetchone()

            if already_sent:
                print("Новость была отправлена ранее")
                continue

            text = f"🔥 <b>{line.text}</b>\n\n🔗 <a href='{line['href']}'> Читать новость</a>"

            try:
                msg = await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode="HTML")
                print(f"Отправлена новая новость. Id: {msg.message_id}")

                await db.execute("INSERT INTO sent_news (url) VALUES (?)", (news_url,))
                await db.commit()

            except Exception as e:
                print(f"Возникла ошибка отправки в Telegram: {e}")

            await asyncio.sleep(1)
        print("Процесс завершён")


async def main():
    await init_db()

    while True:
        try:
            print("Запуск проверки новостей.")
            await parse_and_send()
            print("Проверка окончена. Засыпаю на 10 минут.")
        except Exception as e:
            print(f"Возникла ошибка в цикле - {e}")

        await asyncio.sleep(600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")