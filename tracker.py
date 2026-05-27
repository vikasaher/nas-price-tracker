import requests
import json
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]

PRODUCT = {
    "name": "Toshiba N300 Pro 14TB NAS HDD (HDWG51EXZSTB)",
    "urls": [
        "https://www.walmart.com/ip/1424840852",
                # ADD AMAZON HERE (example format)
        "https://www.amazon.com/Western-Digital-14TB-Internal-Drive/dp/B0CD2XBZWR/ref=sr_1_4?crid=XT25DW915IRC&dib=eyJ2IjoiMSJ9.LCyBOohuZVlpbqpBHfgS91AQFs9-lD3x1RKb9Z-XUrJJZP0rE7Hg5I-CF_UoZ3TpSG8RHRplpn2BWDoXg2FHKX8H3Krm7oTVBRGaKfM31UMpc4MYDbvUSq-CKUUqinSteUr9LKlb2PsqIktArP-hshulI3XsMZrYGwKuDsv6aN5gPmR-E7olUdkGljW_Y7Wp-5xy2s42OrugG8vdwXJTsuP8-LglrSNh4445DRn5ejU.g5o1ppSs5mAkwzU7K0KA4Bi3YifQZvb35X0Bve97tKo&dib_tag=se&keywords=14+TB+NAS+HDD&qid=1779919770&sprefix=14+tb+nas+hdd%2Caps%2C194&sr=8-4",

        # ADD NEWEGG HERE
        https://www.newegg.com/toshiba-n300-pro-hdwg51exzstb-14tb/p/N82E16822149807"
    ]
}

STATE_FILE = "state.json"


# ---------------- STORAGE ----------------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"chat_id": None, "prices": {}}
    return json.load(open(STATE_FILE))


def save_state(state):
    json.dump(state, open(STATE_FILE, "w"), indent=2)


# ---------------- TELEGRAM ----------------

def send(chat_id, msg):
    if not chat_id:
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": msg},
        timeout=15
    )


def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    r = requests.get(url, timeout=15)
    return r.json()


# ---------------- PRICE ----------------

def extract_price(text):
    prices = re.findall(r"\$(\d+\.\d{2})", text)
    if not prices:
        return None
    return min(float(p) for p in prices)


def get_walmart_price(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)

    prices = extract_price(r.text)
    return prices


def get_price(url):
    return get_walmart_price(url)


# ---------------- CHAT ID AUTO-SETUP ----------------

def get_or_set_chat_id(state):
    if state["chat_id"]:
        return state["chat_id"]

    data = get_updates()

    try:
        chat_id = data["result"][-1]["message"]["chat"]["id"]
        state["chat_id"] = chat_id
        save_state(state)
        return chat_id
    except:
        return None


# ---------------- MAIN ----------------

def main():
    state = load_state()

    chat_id = get_or_set_chat_id(state)

    if not chat_id:
        return

    url = PRODUCT["urls"][0]
    price = get_price(url)

    if price is None:
        return

    last = state["prices"].get(PRODUCT["name"])

    # first run
    if last is None:
        state["prices"][PRODUCT["name"]] = price
        save_state(state)
        send(chat_id, f"📦 Tracking started\n{PRODUCT['name']}\nCurrent: ${price}")
        return

    # price drop only
    if price < last - 10:
        send(
            chat_id,
            f"🔻 PRICE DROP\n\n"
            f"{PRODUCT['name']}\n"
            f"Old: ${last}\n"
            f"New: ${price}\n\n"
            f"{url}"
        )
        state["prices"][PRODUCT["name"]] = price
    else:
        state["prices"][PRODUCT["name"]] = last

    save_state(state)


main()
