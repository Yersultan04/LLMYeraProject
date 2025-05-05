# handlers.py

import re
from telegram import Update, InputFile
from telegram.ext import CallbackContext
from dadata_service import get_company_from_dadata
from data_newton_service import get_info_from_data_newton
from llm_service import llm_call_1_yandex
from file_storage import save_case

# 🔍 Извлечение ИНН/ОГРН/названия из произвольного текста
def extract_query(text: str):
    inn_match = re.search(r"\b\d{10}\b", text)
    ogrn_match = re.search(r"\b\d{13}\b", text)
    if inn_match:
        return inn_match.group()
    elif ogrn_match:
        return ogrn_match.group()
    return text.strip()

# 🟢 Старт
def handle_start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Отправь ИНН, ОГРН или название компании для анализа.")

# ⚙️ Главная логика
def handle_message(update: Update, context: CallbackContext):
    raw_text = update.message.text.strip()
    query = extract_query(raw_text)

    update.message.reply_text(f"🔍 Ищу компанию: {query}...")

    company_data = get_company_from_dadata(query)
    if "error" in company_data:
        update.message.reply_text("❌ Ошибка DaData.")
        return

    # ➕ DataNewton
    dn_data = get_info_from_data_newton(company_data["ИНН"])
    if "error" in dn_data:
        update.message.reply_text(f"⚠️ Ошибка DataNewton: {dn_data['error']}")
    else:
        company_data["DataNewton"] = dn_data

        # ⚠️ Автоматическое предупреждение
        negative = dn_data.get("company", {}).get("negative_lists")
        if negative:
            update.message.reply_text("⚠️ Обнаружены негативные признаки")
        else:
            update.message.reply_text("✅ Негативных признаков не найдено")

    # 🧠 LLM-анализ
    llm1 = llm_call_1_yandex(company_data)

    # 💾 Сохраняем
    json_path, txt_path = save_case(query, company_data, llm1)

    # 📎 Отправка пользователю
    update.message.reply_text("📄 Отправляю файлы анализа...")
    with open(txt_path, "rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(f))
    with open(json_path, "rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(f))
