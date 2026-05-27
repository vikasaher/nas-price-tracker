import requests
import json
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://www.walmart.com/ip/1424840852"
STATE_FILE = "state.json"

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )

def get_price():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(URL, headers=headers)
    prices = re.findall(r"\$(\d+\.\d{2})", r.text)
    if not prices:
        return None
    return min(float(p) for p in prices)

def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return json.load(open(STATE_FILE))

def save_state(price):
    json.dump({"price": price}, open(STATE_FILE, "w"))

def main():
    price = get_price()
    if price is None:
        return

    state = load_state()

    if state is None:
        save_state(price)
        send(f"📦 Tracking started\nCurrent price: ${price}")
        return

    last = state["price"]

    if price < last:
        send(f"🔻 PRICE DROP!\nOld: ${last}\nNew: ${price}\n{URL}")
        save_state(price)
    else:
        save_state(last)

main()
