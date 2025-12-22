from bs4 import BeautifulSoup
import requests

def dollarValue():
    url = 'https://www.tgju.org/profile/price_dollar_rl'
    try:
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")
        element = soup.find("span", class_="price")
        current_dollar_price = int(int(element.text.replace(",", "")) / 10)
        return current_dollar_price
    except Exception as e:
        print(e)
        return 0