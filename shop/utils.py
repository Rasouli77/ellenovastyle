import requests
from core import settings


def send_request_to_stock_management(product_code, stock):
    url = "http://artinogroup.ir/api/stock-update/"
    headers = {
        "X-Api-Key": settings.MANAGEMENT_API_KEY,
        "Content-Type": "application/json",
    }
    data = {"product_code": product_code, "stock": stock}
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"error: {e}")
