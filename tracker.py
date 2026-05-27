import requests
import json
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

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


# ---------------- TELEGRAM ----------------

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=15
        )
    except:
        pass


# ---------------- SAFE PRICE PARSING ----------------

def safe_min_price(prices):
    valid = []
    for p in prices:
        try:
            val = float(p)
            if 10 < val < 10000:  # filter garbage
                valid.append(val)
        except:
            continue
    return min(valid) if valid else None


def extract_prices(text):
    return re.findall(r"\$(\d+\.\d{2})", text)


# ---------------- WALMART (IMPROVED) ----------------

def get_walmart_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # Try script JSON blocks first
    scripts = soup.find_all("script")
    for s in scripts:
        if not s.string:
            continue
        if "price" in s.string and "currency" in s.string:
            matches = re.findall(r'"price":\s*(\d+\.\d{2})', s.string)
            price = safe_min_price(matches)
            if price:
                return price

    # fallback
    prices = extract_prices(r.text)
    return safe_min_price(prices)


# ---------------- AMAZON (STABLE FALLBACK) ----------------

def get_amazon_price(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)

    # Amazon blocks scraping often → fallback only
    prices = extract_prices(r.text)
    return safe_min_price(prices)


# ---------------- NEWEGG ----------------

def get_newegg_price(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)

    prices = extract_prices(r.text)
    return safe_min_price(prices)


# ---------------- ROUTER ----------------

def get_price(url):
    if "walmart.com" in url:
        return get_walmart_price(url)
    if "amazon" in url:
        return get_amazon_price(url)
    if "newegg" in url:
        return get_newegg_price(url)

    prices = extract_prices(requests.get(url).text)
    return safe_min_price(prices)


# ---------------- STATE ----------------

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------- MAIN ENGINE ----------------

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
        save_state(state)
        send(f"📦 Tracking started\n{PRODUCT['name']}\nCurrent best: ${best_price}")
        return

    # anti-noise rule
    if best_price < last - 10:
        send(
            f"🔻 BULLET PROOF PRICE DROP\n\n"
            f"{PRODUCT['name']}\n"
            f"Old: ${last}\n"
            f"New: ${best_price}\n\n"
            f"Best deal:\n{best_url}"
        )
        state[PRODUCT["name"]] = best_price
    else:
        state[PRODUCT["name"]] = last

    save_state(state)


main()
