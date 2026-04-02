import hashlib
import hmac
import os
import time
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

HOST = os.getenv("SHOPEE_HOST", "https://partner.shopeemobile.com")
PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID", "")
PARTNER_KEY = os.getenv("SHOPEE_PARTNER_KEY", "")
PARTNER_KEY_BYTES = PARTNER_KEY.encode()
REDIRECT_URL = os.getenv("SHOPEE_REDIRECT_URL", "")


PARTNER_CODE = os.getenv("PARTNER_CODE", "")
SHOP_ID_CODE = os.getenv("SHOP_ID", "")


def _partner_id_payload_value(partner_id: str):
    return int(partner_id) if str(partner_id).isdigit() else partner_id

def get_authorization_link() -> str:
    timest = int(time.time())
    path = "/api/v2/shop/auth_partner"

    base_string = f"{PARTNER_ID}{path}{timest}".encode()
    sign = hmac.new(PARTNER_KEY_BYTES, base_string, hashlib.sha256).hexdigest()

    auth_url = (
        f"{HOST}{path}?partner_id={PARTNER_ID}&timestamp={timest}"
        f"&sign={sign}&redirect={REDIRECT_URL}"
    )
    print(f"Authorization link: {auth_url}")
    return auth_url


def get_access_token(code, shop_id):
    timest = int(time.time())
    path = "/api/v2/auth/token/get"

    base_string = f"{PARTNER_ID}{path}{timest}".encode()
    sign = hmac.new(PARTNER_KEY_BYTES, base_string, hashlib.sha256).hexdigest()

    url = f"{HOST}{path}?partner_id={PARTNER_ID}&timestamp={timest}&sign={sign}"

    payload = {
        "code": code,
        "shop_id": int(shop_id),
        "partner_id": _partner_id_payload_value(PARTNER_ID),
    }

    res = requests.post(url, json=payload)
    print("request_payload:", payload)
    print("request_url:", url)
    print("response_status:", res.status_code, res.reason)

    try:
        data = res.json()
    except ValueError:
        data = {"raw_text": res.text}

    if not res.ok:
        print("response_headers:", dict(res.headers))
        print("response_body:", data)
        request_id = data.get("request_id") if isinstance(data, dict) else None
        if request_id:
            print("request_id:", request_id)
    print(data)
    return data

# first time request token
def get_token_shop_level(code, partner_id, shop_id):
    timest = int(time.time())
    path = "/api/v2/auth/token/get"
    body = {
        "code": code,
        "shop_id": int(shop_id),
        "partner_id": _partner_id_payload_value(partner_id),
    }
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(PARTNER_KEY_BYTES, base_string, hashlib.sha256).hexdigest()
    url = HOST + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    # print(url)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    print("resp", resp)
    ret = resp.json()
    print("ret", ret)
    if ret.get("error") == "invalid_partner_id":
        print(
            f"Config issue: invalid partner_id={partner_id} on host={HOST}. "
            "Check SHOPEE_PARTNER_ID and whether it matches sandbox/production host."
        )
    
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")
    print("value", access_token, new_refresh_token)
    return access_token, new_refresh_token


def get_token_account_level(code, partner_id, main_account_id):
    timest = int(time.time())
    # host = "https://openplatform.sandbox.test-stable.shopee.sg"
    host = " https://openplatform.sandbox.test-stable.shopee.sg/api/v2/auth/token/get"
    
    path = "/api/v2/auth/token/get"
    body = {
        "code": code,
        "main_account_id": int(main_account_id),
        "partner_id": _partner_id_payload_value(partner_id),
    }
    tmp_base_string = "%s%s%s" % (partner_id, path, timest)
    base_string = tmp_base_string.encode()
    sign = hmac.new(PARTNER_KEY_BYTES, base_string, hashlib.sha256).hexdigest()
    url = host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)

    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=body, headers=headers)
    
    print(resp)
    ret = resp.json()
    
    print(ret)
    
    access_token = ret.get("access_token")
    new_refresh_token = ret.get("refresh_token")
    return access_token, new_refresh_token

if __name__ == "__main__":
    # get_authorization_link()
    
    get_access_token(PARTNER_CODE, SHOP_ID_CODE)
    # get_token_shop_level(PARTNER_CODE, PARTNER_ID, SHOP_ID_CODE )