# main.py — Namoz vaqtlari boti (O'zbek tili, xavfsiz, to'g'ri shaharlar bilan)

import asyncio
import json
import aiohttp
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 🔑 O'ZINGIZNING BOT TOKENINGIZNI SHU YERGA YOZING!
BOT_TOKEN = "8202083107:AAGv6bMxZNn2i9WnHJ1kvkQRPVjeRHtFmKQ"

# Qo'llab-quvvatlanadigan shaharlar ro'yxati (O'zbekiston)
UZ_CITIES = [
    "Toshkent", "Samarqand", "Buxoro", "Andijon", "Namangan", "Farg'ona", "Qarshi", "Navoiy",
    "Jizzax", "Xiva", "Urganch", "Nukus", "Termiz", "Shahrisabz", "Guliston", "Angren",
    "Chirchiq", "Qo'qon", "Marg'ilon", "Olmaliq", "Bekobod", "Asaka", "Zomin", "Kattaqo'rg'on"
]

# Logging
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Namoz vaqtlarini olish
async def get_prayer_times(city: str):
    url = "https://api.aladhan.com/v1/timingsByCity"
    params = {
        "city": city,
        "country": "Uzbekistan",
        "method": 2,   # Toshkent (Jafari) usuli
        "school": 0    # Shofe'iy
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # API javobini to'g'ri tekshirish
                    if not data.get("data") or not data["data"].get("timings"):
                        return None
                    return {
                        "city": city,
                        "date": data["data"]["date"]["gregorian"]["date"],
                        "timings": data["std"]["timings"] if "std" in data["data"] else data["data"]["timings"]
                    }
                else:
                    return None
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        return None

# Namoz vaqtlarini faylga saqlash
def save_to_file(data):
    city_clean = data["city"].replace(" ", "_").replace("'", "")
    date_clean = data["date"].replace("-", "_")
    filename = f"{city_clean}_{date_clean}_namoz.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Saqlandi: {filename}")

# /start komandasi
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Assalomu alaykum! 🌙\n\nMen — Namoz vaqtlari botiman.\n\n"
        "Quyidagi ko'rinishda so'rov yuboring:\n<code>/namoz Toshkent</code>\n\n"
        "Qo'llab-quvvatlanadigan shaharlar: Toshkent, Samarqand, Buxoro, Andijon va boshqalar.",
        parse_mode="HTML"
    )

# /namoz komandasi
@dp.message(Command("namoz"))
async def handle_namoz(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Iltimos, shahar nomini kiriting:\nNamuna: <code>/namoz Toshkent</code>",
            parse_mode="HTML"
        )
        return

    city = parts[1].strip().title()

    # 1. Raqam kiritilganmi?
    if city.isdigit():
        await message.answer("❌ Raqam kiritildi. Iltimos, shahar nomini yozing.")
        return

    # 2. Shahar roʻyxatda bormi?
    if city not in UZ_CITIES:
        # O'zbek tilidagi shahar nomlarini tekshirish
        if city.replace("'", "").replace(" ", "") not in [c.replace("'", "").replace(" ", "") for c in UZ_CITIES]:
            await message.answer(
                "❌ Bu shahar hozircha qo'llab-quvvatlanmaydi yoki noto'g'ri yozildi.\n\n"
                "Qo'llab-quvvatlanadigan shaharlar:\n"
                "Toshkent, Samarqand, Buxoro, Andijon, Namangan, Farg'ona, Qarshi, Navoiy, Jizzax, Xiva, Nukus va boshqalar."
            )
            return

    await message.answer(f"⏳ {city} uchun namoz vaqtlari qidirilmoqda...")

    prayer_data = await get_prayer_times(city)
    if not prayer_data:
        await message.answer("❌ Shahar topilmadi yoki tarmoqda muammo. Iltimos, qaytadan urinib ko'ring.")
        return

    # Saqlash
    save_to_file(prayer_data)

    # O'zbekcha nomlar
    uzbek_names = {
        "Fajr": "Bomdod",
        "Sunrise": "Quyosh",
        "Dhuhr": "Peshin",
        "Asr": "Asr",
        "Maghrib": "Shom",
        "Isha": "Xufton"
    }
    order = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

    text = f"🕌 <b>{city}</b> shahri uchun namoz vaqtlari ({prayer_data['date']})\n\n"
    for key in order:
        time = prayer_data["timings"].get(key)
        if time:
            uzb_name = uzbek_names.get(key, key)
            text += f"<b>{uzb_name}:</b> {time}\n"

    await message.answer(text, parse_mode="HTML")

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🤖 Namoz vaqtlari boti ishga tushdi...")
    asyncio.run(main())