import hashlib
import json
import pickle
import time

from seleniumbase import BaseCase

import screenshot


def open_the_form_turnstile_page(sb: BaseCase, url):
    sb.driver.uc_open_with_reconnect(
        url,
        reconnect_time=2.7,
    )


def click_turnstile_and_verify(sb: BaseCase):
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


def is_logged_in(sb: BaseCase):
    if not is_homepage_loaded(sb):
        screenshot.take(sb)
        exit(code=1)

    try:
        return sb.get_current_url() == "https://www.crunchyroll.com/discover"
    except:
        screenshot.take(sb)
        return sb.is_element_present(by="css selector", selector="div[class^='erc-authenticated-user']")


def select_profile(sb: BaseCase):
    is_profile_select_page = sb.is_element_present(by="css selector", selector="img[data-t='profile-avatar']")
    if is_profile_select_page:
        sb.click(selector="img[data-t='profile-avatar']", by="css selector")
        is_homepage_loaded(sb)
        return True


def is_homepage_loaded(sb: BaseCase, selector=".shell-body", timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        is_loading = sb.is_element_present(by="css selector", selector=selector)
        if is_loading or "sso.crunchyroll.com" in sb.get_current_url():
            sb.wait(1)
            continue
        select_profile(sb)
        return True
    print("❌ Home page not loaded in time")
    return False


def load_credentials():
    try:
        with open("credentials.json", "r") as f:
            credentials = json.load(f)
            return credentials
    except FileNotFoundError:
        print("❌ Error: credentials.json not found.")
    except PermissionError:
        print("❌ Error: Permission denied while accessing credentials.json.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while loading credentials.json: {e}")
    exit(1)


def cookie_file_name(credentials=None):
    try:
        if credentials is None:
            credentials = load_credentials()
        hashed_email = hashlib.sha256(credentials["email"].encode("utf-8-sig")).hexdigest()
        return f"crunchyroll_cookies_{hashed_email}.pkl"
    except Exception as e:
        print(f"❌ Failed to get cookie file name: {e}")
    exit(1)


def login(sb: BaseCase):
    sb.execute_script(f'window.location.href = "https://www.crunchyroll.com/"')

    sb.wait_for_element_present(by="css selector", selector="a.cr-login-button", timeout=10)
    screenshot.take(sb)
    sb.click(selector="a.cr-login-button", by="css selector", timeout=10)
    screenshot.take(sb)
    credentials = load_credentials()
    sb.wait_for_element_present(selector="input[name='email']", by="css selector", timeout=10)
    screenshot.take(sb)
    sb.type(selector="input[name='email']", text=credentials["email"])
    screenshot.take(sb)
    sb.type(selector="input[type='password']", text=credentials["password"])
    screenshot.take(sb)
    sb.click(selector="button[data-t='login-button']", by="css selector")
    screenshot.take(sb)
    # Save cookies
    if not is_homepage_loaded(sb):
        screenshot.take(sb)
        print("⏳ Check this credentials.json or try again")
        exit(code=1)
    screenshot.take(sb)
    cookies = sb.get_cookies()
    with open(cookie_file_name(credentials), "wb") as f:
        pickle.dump(cookies, f)
    print("✅ Logged in")
