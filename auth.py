import hashlib
import json
import pickle
import time

import screenshot


def open_the_form_turnstile_page(sb, url):
    sb.driver.uc_open_with_reconnect(
        url,
        reconnect_time=2.7,
    )


def click_turnstile_and_verify(sb):
    sb.scroll_to_bottom()
    sb.driver.uc_switch_to_frame("iframe")
    sb.driver.uc_click("span.mark")
    sb.highlight("img#captcha-success", timeout=3.33)


def try_bypass_turnstile(sb, url):
    open_the_form_turnstile_page(sb, url)
    try:
        click_turnstile_and_verify(sb)
    except Exception:
        open_the_form_turnstile_page(sb, url)


def is_logged_in(sb):
    if not is_homepage_loaded(sb):
        screenshot.take(sb)
        exit(code=1)

    try:
        sb.wait_for_element("css selector", ".header-actions .user-actions-item", timeout=10)
        return sb.is_element_present("css selector", "div[class^='erc-authenticated-user']")
    except:
        screenshot.take(sb)
        return sb.is_element_present("css selector", "div[class^='erc-authenticated-user']")


def select_profile(sb):
    is_profile_select_page = sb.is_element_present("css selector", "img[data-t='profile-avatar']")
    if is_profile_select_page:
        sb.click("img[data-t='profile-avatar']", by="css selector")
        is_homepage_loaded(sb)
        return True


def is_homepage_loaded(sb, selector=".shell-body", timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        is_loading = sb.is_element_present("css selector", selector)
        if is_loading or "sso.crunchyroll.com" in sb.driver.current_url:
            sb.wait(1)
            continue
        select_profile(sb)
        return True
    print("Home page not loaded in time")
    return False


def load_credentials():
    try:
        with open("credentials.json", "r") as f:
            credentials = json.load(f)
            return credentials
    except FileNotFoundError:
        print("Error: credentials.json not found.")
    except PermissionError:
        print("Error: Permission denied while accessing credentials.json.")
    except Exception as e:
        print(f"An unexpected error occurred while loading credentials.json: {e}")
    exit(1)


def cookie_file_name(credentials=None):
    try:
        if credentials is None:
            credentials = load_credentials()
        hashed_email = hashlib.sha256(credentials["email"].encode("utf-8-sig")).hexdigest()
        return f"crunchyroll_cookies_{hashed_email}.pkl"
    except Exception as e:
        print(f"Failed to get cookie file name: {e}")
    exit(1)


def login(sb):
    try_bypass_turnstile(
        sb,
        "https://sso.crunchyroll.com/authorize?client_id=noaihdevm_6iyg0a8l0q&redirect_uri=https%3A%2F%2Fwww.crunchyroll.com%2Fcallback&response_type=cookie&state=%2F",
    )
    credentials = load_credentials()
    sb.type("input[name='email']", credentials["email"])
    sb.type("input[type='password']", credentials["password"])
    sb.click("button[data-t='login-button']", by="css selector")
    screenshot.take(sb)
    # Save cookies
    if not is_homepage_loaded(sb):
        screenshot.take(sb)
        print("Check this credentials.json or try again")
        exit(code=1)
    screenshot.take(sb)
    cookies = sb.driver.get_cookies()
    with open(cookie_file_name(credentials), "wb") as f:
        pickle.dump(cookies, f)
    print("Logged in")
