import argparse
import glob
import os
import pickle
import textwrap

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


def parse_args():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [url] [-h] [-l en-US vi-VN ...] [-s -1 1 2 ...] [-L NUMBER] [-f]",
        description="Crunchyroll subtitles downloader",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("url", nargs="?", help="Crunchyroll episode or series URL")
    parser.add_argument(
        "-l",
        "--lang",
        help=textwrap.dedent(
            """\
            List of languages to download subtitles for. E.g: -l vi-VN en-US.
            If using with "animes.json" file, it will override the "lang" specified in animes.json.
            If using with "url" argument:
                It will download subtitles for specified languages.
                If not specified, will download subtitles for all languages.

            Example:
                -l vi-VN en-US    will download subtitles for languages vi-VN and en-US. Override all the "lang" specified in animes.json.

            """
        ),
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "-s",
        "--season",
        help=textwrap.dedent(
            """\
            List of seasons number to download subtitles for.
            If using with "animes.json" file, it will override the "seasons" specified in animes.json.
            If using with "url" argument:
                It will download subtitles for specified seasons.
                If not specified, will download subtitles for all seasons.
            Will be ignored for episode URL.

            Example:
                -s 1 2   will download subtitles for seasons 1 and 2.
                -s -1    will download subtitles for the latest season.

            """
        ),
        type=int,
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "-L",
        "--latest",
        help=textwrap.dedent(
            """\
            Number of latest/newest episodes to download subtitles for.
            If using with "animes.json" file, it will override the "latest" specified in animes.json.
            If using with "url" argument:
                It will download subtitles for specified number of latest/newest episodes.
            Will be ignored for episode URL.

            Examples:
                -L 3         Download subtitles for the latest 3 episodes of all seasons.
                -L 3 -s 1 2  Download subtitles for the latest 3 episodes of seasons 1 and 2.
                -L 1 -s -1   Download subtitles for only the newest episode of the newest season.

            """
        ),
        type=int,
    )
    parser.add_argument(
        "-f", "--force", help="Force to download even if the subtitles is already downloaded", action="store_true"
    )
    args = parser.parse_args()

    url = args.url
    lang = args.lang or []
    seasons = args.season or []
    force = args.force or False
    get_latest_n_episodes = args.latest or None
    return url, lang, seasons, force, get_latest_n_episodes


def main():
    url, lang, seasons, force, get_latest_n_episodes = parse_args()
    print("⏳ Opening browser...")
    with SB(
        uc=True,
        headless=True,
        chromium_arg=(
            "--headless=new,--mute-audio,--window-size=1920,1080,--disable-gpu,--disable-dev-shm-usage,--no-sandbox"
        ),
    ) as sb:
        init_files()
        cookies_file = auth.cookie_file_name()
        if os.path.exists(cookies_file):
            sb.open("https://www.crunchyroll.com")
            print("🧑‍🍳🍪 Checking cookies...")
            try:
                with open(cookies_file, "rb") as f:
                    cookies = pickle.load(f)

                for cookie in cookies:
                    sb.driver.add_cookie(cookie)
            except Exception:
                print("⚠️ Invalid cookie, removing cookies")
                if os.path.exists(cookies_file):
                    os.remove(cookies_file)
                sb.driver.delete_all_cookies()
            sb.driver.refresh()
            if auth.is_logged_in(sb):
                screenshot.take(sb)
                print("♻️ Reusing old cookies")
            else:
                screenshot.take(sb)
                print("⚠️ Invalid cookies, logging in...")
                auth.login(sb)
        else:
            print("⚠️ No cookies, logging in...")
            auth.login(sb)
        animes.start_download_anime(sb, url, lang, seasons, force, get_latest_n_episodes)


if __name__ == "__main__":
    main()
