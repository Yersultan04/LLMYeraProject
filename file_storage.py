# file_storage.py

import os
import json
from datetime import datetime
from config import SAVE_PATH


def ensure_save_path():
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)


def format_detailed_txt(company_data, llm1_json):
    entity = llm1_json.get("Entity Recognition", {})
    summary = llm1_json.get("Text Summary", "")
    risks = llm1_json.get("Risks", [])
    classification = llm1_json.get("Classification", "")

    lines = []

    lines.append("📌 Entity Recognition:")
    for k, v in entity.items():
        lines.append(f"- {k}: {v}")

    lines.append("\n🧠 Text Summary:")
    lines.append(summary or "—")

    lines.append("\n⚠️ Risks:")
    if risks:
        lines.extend([f"- {r}" for r in risks])
    else:
        lines.append("- Не обнаружено")

    lines.append(f"\n📊 Classification: {classification}")

    return "\n".join(lines)


def save_case(company_name, company_data, llm1):
    ensure_save_path()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = company_name.replace(" ", "_").replace("\"", "").replace("«", "").replace("»", "")

    case = {
        "timestamp": timestamp,
        "company_name": company_name,
        "company_data": company_data,
        "llm_call_1": llm1
    }

    json_path = os.path.join(SAVE_PATH, f"{safe_name}_{timestamp}.json")
    txt_path = os.path.join(SAVE_PATH, f"{safe_name}_{timestamp}.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)

    # Формируем подробный текстовый отчёт
    if "json" in llm1:
        text = format_detailed_txt(company_data, llm1["json"])
    else:
        text = llm1.get("text", "⚠️ Анализ не удалось выполнить.")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return json_path, txt_path
