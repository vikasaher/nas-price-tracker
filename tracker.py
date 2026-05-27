import requests
import json
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PRODUCT = {
    "name": "Toshiba N300 Pro 14TB NAS HDD",
    "urls": [
        "https://www.walmart.com/ip/1424840852",
        # You will later add Amazon + Newegg links here
    ]
}

STATE_FILE = "state.json"


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )


# ---------- RELIABLE PRICE EXTRACTION ----------

def extract_price(text):
    prices = re.findall(r"\$(\d+\.\d{2})", text)
    if not prices:
        return None
    return min(float(p) for p in prices)


def get_walmart_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    r = requests.get(url, headers=headers, timeout=20)

    # Walmart sometimes embeds JSON in page — this is more stable than raw scraping
    soup = BeautifulSoup(r.text, "html.parser")

    scripts = soup.find_all("script")
    for s in scripts:
        if s.string and "price" in s.string:
            prices = re.findall(r'"price":(\d+\.\d{2})', s.string)
            if prices:
                return float(prices[0])

    # fallback
    return extract_price(r.text)


def get_price(url):
    if "walmart.com" in url:
        return get_walmart_price(url)

    # generic fallback (Amazon / Newegg initial version)
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    return extract_price(r.text)


# ---------- STATE ----------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    return json.load(open(STATE_FILE))


def save_state(state):
    json.dump(state, open(STATE_FILE, "w"), indent=2)


# ---------- MAIN LOGIC ----------

def main():
    state = load_state()

    best_price = None
    best_url = None

    for url in PRODUCT["urls"]:
        price = get_price(url)

        if price is None:
            continue

        if best_price is None or price < best_price:
            best_price = price
            best_url = url

    if best_price is None:
        return

    last = state.get(PRODUCT["name"])

    if last is None:
        state[PRODUCT["name"]] = best_price
        send(f"📦 Tracking started\n{PRODUCT['name']}\nCurrent best: ${best_price}")
        save_state(state)
        return

    # alert only on meaningful drop
    if best_price < last - 10:
        send(
            f"🔻 PRICE DROP ALERT\n\n"
            f"{PRODUCT['name']}\n"
            f"Old: ${last}\n"
            f"New: ${best_price}\n\n"
            f"Best link:\n{best_url}"
        )
        state[PRODUCT["name"]] = best_price

    else:
        state[PRODUCT["name"]] = last

    save_state(state)


main()
