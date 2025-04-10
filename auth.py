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
        if is_loading:
            sb.wait(1)
            continue
        select_profile(sb)
        return True
    print("Home page not loaded in time")
    return False


def login(sb):
    f = open("credentials.json")
    credentials = json.load(f)
    try_bypass_turnstile(
        sb,
        "https://sso.crunchyroll.com/login?return_url=%2Fauthorize%3Fclient_id%3Dnoaihdevm_6iyg0a8l0q%26redirect_uri%3Dhttps%253A%252F%252Fwww.crunchyroll.com%252Fcallback%26response_type%3Dcookie%26state%3D%252F",
    )
    sb.type("input[name='email']", credentials["email"])
    sb.type("input[type='password']", credentials["password"])
    sb.click("button[data-t='login-button']", by="css selector")
    # Save cookies
    if not is_homepage_loaded(sb):
        screenshot.take(sb)
        exit(code=1)
    cookies = sb.driver.get_cookies()
    with open("crunchyroll_cookies.pkl", "wb") as f:
        pickle.dump(cookies, f)
    print("Logged in")
