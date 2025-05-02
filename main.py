import glob
import os
import pickle

from seleniumbase import SB

import animes
import auth
import screenshot


def init_files():
    save_sub_location = os.path.join("output", "downloaded")
    debug_screenshot_location = os.path.join("screenshots")
    saved_downloaded_file = os.path.join("output", "saved_file.json")
    if not os.path.exists("output"):
        os.makedirs("output")
    if not os.path.exists(save_sub_location):
        os.makedirs(save_sub_location)
    if not os.path.exists(debug_screenshot_location):
        os.makedirs(debug_screenshot_location)
    else:
        files = glob.glob(os.path.join("screenshots", "*.png"))
        for file in files:
            os.remove(file)
    if not os.path.exists(saved_downloaded_file):
        f_tmp = open(saved_downloaded_file, "a+")  # open file in append mode
        f_tmp.write("[]")
        f_tmp.close()


def main():
    with SB(uc=True) as sb:
        init_files()
        cookies_file = auth.cookie_file_name()
        if os.path.exists(cookies_file):
            sb.open("https://www.crunchyroll.com")
            print("Checking cookies...")
            try:
                with open(cookies_file, "rb") as f:
                    cookies = pickle.load(f)

                for cookie in cookies:
                    sb.driver.add_cookie(cookie)
            except Exception:
                print("Invalid cookie, removing cookies")
                if os.path.exists(cookies_file):
                    os.remove(cookies_file)
                sb.driver.delete_all_cookies()
            sb.driver.refresh()
            if auth.is_logged_in(sb):
                screenshot.take(sb)
                print("Reusing old cookies")
            else:
                screenshot.take(sb)
                print("Invalid cookies, logging in...")
                auth.login(sb)
        else:
            print("No cookies, logging in...")
            auth.login(sb)
        animes.start_download_anime(sb)


if __name__ == "__main__":
    main()
