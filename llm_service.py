# llm_service.py

import requests
import json
import re
from config import IAM_TOKEN, FOLDER_ID

YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def llm_call_1_yandex(company_data):
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }

    # 🧠 Обновлённый промпт с 4 задачами
    system_prompt = (
        "Ты аналитик юридических лиц. На основе структурированных данных о компании выполни:\n"
        "1. Entity Recognition: выдели ключевые атрибуты (название, ИНН, ОГРН, адрес, учредители и т.п.)\n"
        "2. Text Summarization: сделай краткое резюме состояния компании.\n"
        "3. Risk Pattern Detection: перечисли риски — суды, санкции, банкротство, проблемы с регистрацией и т.д.\n"
        "4. Classification: оцени — 'Все ясно' или 'Нужны дополнительные данные'.\n\n"
        "Верни результат строго в JSON со следующей структурой:\n"
        "{\n"
        "  \"Entity Recognition\": {...},\n"
        "  \"Text Summary\": \"...\",\n"
        "  \"Risks\": [...],\n"
        "  \"Classification\": \"Все ясно\" или \"Нужны дополнительные данные\"\n"
        "}"
    )

    user_prompt = f"Вот информация о компании:\n{json.dumps(company_data, ensure_ascii=False, indent=2)}"

    body = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 700
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt}
        ]
    }

    try:
        response = requests.post(YANDEX_API_URL, headers=headers, json=body).json()
        if "result" in response:
            text = response["result"]["alternatives"][0]["message"]["text"]

            # Убираем обёртки вида ```json ... ```
            clean_text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()

            try:
                parsed = json.loads(clean_text)
                return {"json": parsed, "text": clean_text}
            except Exception as e:
                return {"error": "Ошибка парсинга", "text": text}
        else:
            return {"error": response.get("error", "LLM: Неизвестная ошибка")}
    except Exception as e:
        return {"error": f"LLM: {str(e)}"}
