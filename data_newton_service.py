# data_newton_service.py

import requests

API_KEY = "Y4ixzC9ZyQX6"
BASE_URL = "https://api.datanewton.ru/v1/counterparty"

def get_info_from_data_newton(inn: str):
    try:
        params = {
            "key": API_KEY,
            "inn": inn
            # без filters — базовый ответ
        }

        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"DataNewton: {response.status_code} — {response.text}"
            }
    except Exception as e:
        return {"error": f"DataNewton: {str(e)}"}
