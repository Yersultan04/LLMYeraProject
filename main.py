# 📌 Установка зависимостей (выполни отдельно в терминале, если не установлено)
# pip install python-telegram-bot==13.15 dadata

import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import json
import os
import requests
from dadata import Dadata

# --- Telegram config ---
TELEGRAM_TOKEN = "8138051471:AAEIJXlbAWkHaZFh4M9sGjJ_SEaXJMAqAbE"
SAVE_PATH = "/Users/yersultanakhmer/Desktop/Yera LLM/"
IAM_TOKEN = "t1.9euelZqejMvNns2Pi5Wdk5Gbj5DGlu3rnpWajcnIz5SWmYnLypqUmp6bjJLl8_d4XiA_-e9Mcghd_N3z9zgNHj_570xyCF38zef1656VmsyZkZCQxs-Sz8yUiY-Zy8iM7_zF656VmsyZkZCQxs-Sz8yUiY-Zy8iM.AlcWjDom3NgfgKYu7tt-iSNUenQj9kgBpnGeQA4PSVCo8GxidhnTvyC3EOwQh_6O0ANC3qDrL8gNERS56lVjDw"
FOLDER_ID = "b1g4vc28s14is85ugma9"

# --- DaData config ---
DADATA_API_KEY = "79a44b0222a1cfbb6eec708d21ced8d9ebcbabe8"
DADATA_SECRET = "d36f7177c89c0d2f8817ff90f3dfaa1ced49aa65"
dadata = Dadata(DADATA_API_KEY, DADATA_SECRET)

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Получение компании из DaData ---
def get_company_from_dadata(query: str) -> dict:
    try:
        result = dadata.find_by_id("party", query, count=1)
        if not result:
            return {"error": "Компания не найдена"}

        data = result[0]["data"]
        name = data.get("name", {}).get("full_with_opf", "")
        ogrn = data.get("ogrn", "")
        inn = data.get("inn", "")
        address = data.get("address", {}).get("value", "")
        founders = data.get("management", {}).get("name", "Не указано")
        activity = data.get("okved", "") + " — " + data.get("okved_type", "")

        return {
            "Название": name,
            "ОГРН": ogrn,
            "ИНН": inn,
            "Адрес": address,
            "Финансы": "Нет данных из DaData",
            "Суды": "Нет данных из DaData",
            "Учредители": founders,
            "Вид деятельности": activity
        }

    except Exception as e:
        return {"error": f"Ошибка при обращении к DaData: {str(e)}"}

# --- YandexGPT Call 1 ---
def llm_call_1_yandex(company_data, iam_token, folder_id):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Bearer {iam_token}", "Content-Type": "application/json"}

    system_prompt = "Ты аналитик, делающий предварительный анализ компании..."
    user_prompt = f"Вот информация о компании:\n{company_data}\n\nСделай анализ в JSON."

    body = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": 700},
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=body).json()
    if "result" in response:
        text = response["result"]["alternatives"][0]["message"]["text"]
        try:
            parsed = json.loads(text.strip("`\n "))
            return {"json": parsed, "text": text}
        except:
            return {"error": "LLM 1: Ошибка парсинга", "text": text}
    return {"error": response.get("error", "LLM 1: Неизвестная ошибка")}

# --- YandexGPT Call 2 ---
def llm_call_2_yandex(company_data, additional_info, iam_token, folder_id):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Bearer {iam_token}", "Content-Type": "application/json"}

    system_prompt = "Ты эксперт по due diligence. Сформируй executive_summary."
    user_prompt = f"Компания:\n{company_data}\n\nДополнительно:\n{additional_info}\n\nРезультат в JSON."

    body = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": 700},
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=body).json()
    if "result" in response:
        text = response["result"]["alternatives"][0]["message"]["text"]
        try:
            parsed = json.loads(text.strip("`\n "))
            return {"json": parsed, "text": text}
        except:
            return {"error": "LLM 2: Ошибка парсинга", "text": text}
    return {"error": response.get("error", "LLM 2: Неизвестная ошибка")}

# --- Сохранение файлов ---
def save_case(company_name, company_data, llm1, additional_info=None, llm2=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = company_name.replace(" ", "_")
    case = {
        "timestamp": timestamp,
        "company_name": company_name,
        "company_data": company_data,
        "llm_call_1": llm1
    }
    if additional_info:
        case["additional_info"] = additional_info
    if llm2:
        case["llm_call_2"] = llm2

    json_path = os.path.join(SAVE_PATH, f"{safe_name}_{timestamp}.json")
    txt_path = os.path.join(SAVE_PATH, f"{safe_name}_{timestamp}.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)

    text = llm2["text"] if llm2 and "text" in llm2 else llm1.get("text", "Нет анализа")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return json_path, txt_path

# --- Обработка сообщений ---
def handle_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Привет! Отправь ИНН, ОГРН или название компании, чтобы я провёл анализ."
    )

def handle_message(update: Update, context: CallbackContext):
    query = update.message.text.strip()
    update.message.reply_text(f"🔍 Ищу компанию: {query}...")

    company_data = get_company_from_dadata(query)
    if "error" in company_data:
        update.message.reply_text("❌ Компания не найдена или ошибка DaData.")
        return

    llm1 = llm_call_1_yandex(company_data, IAM_TOKEN, FOLDER_ID)
    needs_extra = llm1.get("json", {}).get("needs_additional_check", False)
    additional_info = "Компания сменила адрес и заключила партнёрство с Wildberries."
    llm2 = llm_call_2_yandex(company_data, additional_info, IAM_TOKEN, FOLDER_ID) if needs_extra else None

    json_file, txt_file = save_case(query, company_data, llm1, additional_info, llm2)

    update.message.reply_text("✅ Анализ завершён. Отправляю файлы...")
    with open(txt_file, "rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(f))
    with open(json_file, "rb") as f:
        context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(f))

# --- Старт бота ---
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", handle_start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
