# dadata_service.py

from dadata import Dadata
from config import DADATA_API_KEY, DADATA_SECRET

dadata = Dadata(DADATA_API_KEY, DADATA_SECRET)

def get_company_from_dadata(query: str) -> dict:
    try:
        # Используем подсказки (suggest), а не find_by_id
        result = dadata.suggest("party", query, count=1)
        if not result:
            return {"error": "Компания не найдена"}

        data = result[0]["data"]

        return {
            "Название": data.get("name", {}).get("full_with_opf", ""),
            "ОГРН": data.get("ogrn", ""),
            "ИНН": data.get("inn", ""),
            "Адрес": data.get("address", {}).get("value", ""),
            "Учредители": data.get("management", {}).get("name", "Не указано"),
            "Вид деятельности": data.get("okved", "") + " — " + data.get("okved_type", "")
        }

    except Exception as e:
        return {"error": f"DaData ошибка: {str(e)}"}
