import copy
import json
import os
import re
import time
import traceback
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from seleniumbase import BaseCase

import screenshot
import subtitle_processor

new_downloaded_subtitles = {}


class AttrDict(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'AttrDict' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return super().get(key, default)

    def set(self, key: str, value: Any) -> None:
        self[key] = value


def start_download_anime(
    sb: BaseCase,
    single_url=None,
    lang=[],
    seasons_override=[],
    force_download=False,
    get_latest_n_episodes: None | int = None,
):
    print("Loading animes list")

    list_downloaded = []
    if not force_download:
        with open(os.path.join("output", "saved_file.json"), "r") as f2:
            list_downloaded = json.load(f2)

    animes = []
    if not single_url:
        f = open("animes.json")
        animes = json.load(f)
    elif any(url in single_url for url in ["/series/", "/watch/"]):
        animes.append({"url": single_url})
    else:
        print(f"Invalid Episode/Series URL: {single_url}")
        exit(code=1)

    for anime in animes:
        if type(anime) == str:
            anime = AttrDict({"url": anime})
        if lang:
            anime["lang"] = copy.deepcopy(lang)
        if seasons_override:
            anime["seasons"] = copy.deepcopy(seasons_override)
        if get_latest_n_episodes:
            anime["latest"] = get_latest_n_episodes

        print(f"--------------------------------------------------------------------------------")
        if not anime.get("url"):
            print("Missing URL in animes.json")
            continue

        anime["lang"] = anime.get("lang") or []
        if "/series/" in anime.get("url"):
            print(f"Checking Series URL: {anime['url']}")
            anime["seasons"] = anime.get("seasons") or []
            latest_season = False
            if anime.get("seasons"):
                for s in anime.get("seasons"):
                    if s < 0:
                        latest_season = True
                        break
            if (not anime.get("seasons")) or latest_season:
                sb.open(anime.get("url"))
                anime["seasons"], _ = get_all_season_indexes(sb) or []
                if latest_season:
                    anime["seasons"] = [anime["seasons"][-1]] if anime["seasons"] else []

            for season in anime["seasons"]:
                handle_season(sb, anime, season, list_downloaded)
        elif "/watch/" in anime.get("url"):
            print(f"Checking epsode URL: {anime.get('url')}")
            handle_single_episode(sb, anime.get("url"), anime.get("lang"), list_downloaded)
        else:
            print(f"Invalid Epsode/Series URL: {anime.get('url')}")

    with open(os.path.join("output", "latest_downloaded.txt"), "w") as f3:
        if new_downloaded_subtitles:
            print(f"--------------------------------------------------------------------------------")
            print(f"New subtitles downloaded:")
            for key, value in new_downloaded_subtitles.items():
                print(f"    {key}:")
                f3.write(f"    {key}:")
                for v in value:
                    f3.write(f"        {v}")
                    print(f"        {v}")
        else:
            print("No new subtitles.")
            f3.write("No new subtitles.")


def handle_season(sb, series, season, list_downloaded):
    if not series.get("url") or int(season) < 1:
        return
    xv = [x for x in list_downloaded if x["url"] == series["url"] and int(x["season"]) == int(season)]
    skip_episodes = list(xv[0]["downloaded"]) if xv else list()
    sb.open(series["url"])

    try:
        print(f"Checking season number: {str(season)}")
        select_season_from_dropdown_list(sb, season)
        click_load_more_btn(sb)
        episode_urls = get_list_of_episode_urls(sb)
        if series.get("latest") and episode_urls:
            episode_urls = episode_urls[-series.get("latest") :]
        total_episodes_episodes = len(episode_urls)

        print(f"Total number of episodes in season {season}: {str(total_episodes_episodes)}")
        open_episode_url(sb, series, season, episode_urls, skip_episodes)
    except:
        traceback.print_exc()


def handle_single_episode(sb: BaseCase, episode_url, lang=[], list_downloaded=[]):
    series = AttrDict()
    series.lang = lang or []
    sb.set_window_size(681, 793)

    sb.open(episode_url)
    series.url = get_series_url_from_watch_page(sb)
    click_see_more_episodes_from_watch_page(sb)
    _, season = get_all_season_indexes(sb)
    close_see_more_episodes_in_watch_page(sb)
    sb.set_window_size(1920, 1080)

    if not season or season <= 0:
        print("No seasons found")
        return

    xv = [x for x in list_downloaded if x["url"] == series["url"] and x["season"] == season]
    skip_episodes = list(xv[0]["downloaded"]) if xv else list()
    try:
        open_episode_url(sb, series, season, [episode_url], skip_episodes, suppress_download_msg=True)
    except:
        traceback.print_exc()


def get_all_season_indexes(sb: BaseCase) -> tuple[list, int]:
    try:
        sb.wait_for_element_present("css selector", ".episode-list .erc-playable-collection", timeout=15)

        if sb.is_element_present("css selector", ".season-info > h4 > span"):
            sb.click(".season-info", by="css selector")
            sb.wait_for_element_present("css selector", "[class^='dropdown-content__children']", timeout=15)

            list_season_el = sb.find_elements(
                "css selector",
                "[class^='dropdown-content__children'] div[class^='extended-option']",
            )

            for index, el in enumerate(list_season_el):
                class_attr = el.get_attribute("class")
                if class_attr and "extended-option--is-active" in class_attr:
                    current_season_number = index + 1

            season_count = len(list_season_el)
            return list(range(1, season_count + 1)), current_season_number
        else:
            return [1], 1

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)
        # accept_consent(sb)
    return [], 0


def click_load_more_btn(sb):
    try:
        while True:
            sb.wait_for_element_present("css selector", "div.erc-season-episode-list", timeout=15)

            if sb.is_element_present("css selector", "[data-t='show-more-btn']"):
                sb.click("[data-t='show-more-btn']", by="css selector")
                sb.wait_for_element_present("css selector", "div.erc-season-episode-list", timeout=15)
            else:
                sb.wait(1)
                break
    except Exception as e:
        print("Cannot click load more")
        print(f"Error: {e}")
        traceback.print_exc()
        return


def select_season_from_dropdown_list(sb, season):
    try:
        sb.wait_for_element_present("css selector", ".episode-list .erc-playable-collection", timeout=15)
        if sb.is_element_present("css selector", ".season-info > h4 > span"):
            sb.click(".season-info", by="css selector")
            sb.wait_for_element_present("css selector", "[class^='dropdown-content__children']", timeout=15)
            sb.click(
                "[class^='dropdown-content__children'] > div > div:nth-child(" + str(season) + ")",
                by="css selector",
            )
            sb.wait_for_element_present("css selector", ".erc-season-episode-list", timeout=15)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)
        # accept_consent(sb)
        return


def open_episode_url(sb, anime, season, episodes_urls=[], skip_episodes=[], suppress_download_msg=False):
    for index, episode_url in enumerate(episodes_urls):

        languages_to_download = []
        languages_to_skip = next((ep["lang"] for ep in skip_episodes if ep["url"] == episode_url), [])
        for lang in anime["lang"]:
            if any(ep["url"] == episode_url and lang in ep["lang"] for ep in skip_episodes):
                continue
            else:
                languages_to_download.append(lang)

        if len(anime["lang"]) > 0 and len(languages_to_download) == 0:
            continue
        if not suppress_download_msg:
            print(f"Checking episode URL: {str(episode_url)}")
        if sb.driver.current_url != episode_url:
            go_to_episode_page(sb, episode_url)
        episode_metadata = get_episode_metadata(sb, season, episode_url)
        if episode_metadata is None:
            continue
        if len(episode_metadata["playService"]["subtitles"]) == 0:
            print("No subtitles found!")
            log_downloaded_episode(anime, season, skip_episodes)
            go_back_to_ep_lists_page(sb, season)
            continue
        downloaded_subtitles = save_episode_subtitles(
            sb, season, episode_metadata, languages_to_download, languages_to_skip
        )
        downloaded_subtitles_langs = sorted(set(d["lang"] for d in downloaded_subtitles))
        skip_episodes = append_lang_to_skip_urls(skip_episodes, episode_url, downloaded_subtitles_langs)
        log_downloaded_episode(anime, season, skip_episodes)
        if len(downloaded_subtitles) > 0:
            print("Downloaded new subtiles: " + ", ".join(downloaded_subtitles_langs))
        if len(languages_to_download) > 0 and len(languages_to_download) != len(downloaded_subtitles_langs):
            print("Missing subtitles: " + ", ".join(d for d in languages_to_download if d not in downloaded_subtitles))
        go_back_to_ep_lists_page(sb, season)


def get_episode_metadata(sb: BaseCase, season, episode_url, attempts=3):
    if attempts == 0:
        print("Error getting episode metadata")
        return
    try:
        iframe = sb.wait_for_element_present("css selector", "iframe.video-player", timeout=15)
        sb.driver.switch_to.frame(iframe)

        if wait_for_video_to_play(sb, "video", timeout=15):
            screenshot.take(sb)
            metadata = json.loads(sb.execute_script("return JSON.stringify(self.v1config.media)"))
            sb.driver.switch_to.default_content()
            return metadata
        screenshot.take(sb)
        sb.driver.switch_to.default_content()
    except:
        print("Error getting episode metadata, Retrying...")
        iframe = sb.wait_for_element_present("css selector", "iframe.video-player", timeout=15)
        sb.driver.switch_to.frame(iframe)
        stop_video_play(sb)
        sb.driver.switch_to.default_content()
        slowdown_if_restrictions_overlay(sb)
        go_back_to_ep_lists_page(sb, season)
        go_to_episode_page(sb, episode_url)
        return get_episode_metadata(sb, season, episode_url, attempts - 1)


def safe_filename(name, replacement="_", max_length=255):
    # Replace invalid characters with the replacement character
    safe = re.sub(r'[\\/:*?"<>|]', replacement, name).strip()
    return safe[:max_length]


def save_episode_subtitles(sb, season, tvshow_info, lang_to_download=[], downloaded_language=[]):
    subtitles = []
    list_subtitle_from_crunchyroll = tvshow_info["playService"]["subtitles"]
    series_title = safe_filename(tvshow_info["metadata"]["series_title"])
    season_title = safe_filename(tvshow_info["metadata"]["season_title"])
    ep_title = safe_filename(tvshow_info["metadata"]["title"])

    save_folder = os.path.join(
        "output",
        "downloaded",
        series_title,
        season_title,
    )

    for subtitle in list_subtitle_from_crunchyroll:
        if (
            list_subtitle_from_crunchyroll[subtitle]["language"] == "none"
            or (lang_to_download and list_subtitle_from_crunchyroll[subtitle]["language"] not in lang_to_download)
            or (downloaded_language and list_subtitle_from_crunchyroll[subtitle]["language"] in downloaded_language)
        ):
            continue
        save_filename = "".join(
            [
                tvshow_info["metadata"]["display_episode_number"],
                " - ",
                ep_title,
                ".",
                list_subtitle_from_crunchyroll[subtitle]["language"],
                ".",
                list_subtitle_from_crunchyroll[subtitle]["format"],
            ]
        )
        sb.save_file_as(list_subtitle_from_crunchyroll[subtitle]["url"], save_filename, save_folder)
        output = os.path.join(save_folder, save_filename)

        subtitles.append(
            {
                "lang": list_subtitle_from_crunchyroll[subtitle]["language"],
                "url": output,
            }
        )
        if list_subtitle_from_crunchyroll[subtitle]["language"] == "vi-VN":
            subtitle_processor.remove_unused_styles(output, output, is_replace_font=True)
        else:
            subtitle_processor.remove_unused_styles(output, output, is_replace_font=False)
        add_new_downloaded_subtitle(
            tvshow_info["metadata"]["series_title"],
            f"S{str(season)}E{tvshow_info["metadata"]["display_episode_number"]} ({list_subtitle_from_crunchyroll[subtitle]["language"]}): {tvshow_info["metadata"]["title"]}",
        )
    return subtitles


def log_downloaded_episode(anime, season, downloaded_episodes=[]):
    f = open(os.path.join("output", "saved_file.json"), "r+")
    data = json.load(f)
    data = [x for x in data if x["url"] != anime["url"] or x["season"] != season]
    data.append(
        {
            "url": anime["url"],
            "season": season,
            "downloaded": downloaded_episodes,
        }
    )
    f.seek(0)  # Move the file pointer to the beginning of the file
    json.dump(data, f, indent=2)
    f.truncate()  # Truncate the remaining content (if any)
    f.close()


def append_lang_to_skip_urls(skip_episodes, episode_url, episode_langs):
    for downloaded in skip_episodes:
        if downloaded["url"] == episode_url:
            # Merge languages without duplicates
            downloaded["lang"] = list(set(downloaded["lang"]) | set(episode_langs))
            return skip_episodes

    # If not found, add new entry
    skip_episodes.append({"url": episode_url, "lang": list(set(episode_langs))})
    return skip_episodes


def get_list_of_episode_urls(sb):
    print("Getting list of episode")
    element = sb.wait_for_element_present("css selector", ".episode-list .erc-playable-collection", timeout=15)
    base_url = sb.get_current_url()
    if element:
        return [
            urljoin(base_url, el.get_attribute("href"))
            for el in sb.driver.find_elements(
                "css selector",
                ".episode-list .erc-playable-collection .card a[class^='playable-card-hover__link']",
            )
            if el.get_attribute("href")
        ]

    return []
    # return sb.execute_script("return document.querySelectorAll('.card').length")


def wait_for_video_to_play(sb: BaseCase, selector="video", timeout=15):
    start = time.time()
    sb.wait_for_element_present("css selector", selector, timeout)
    while time.time() - start < timeout:
        is_playing = sb.execute_script(
            f"""
            var video = document.querySelector("{selector}");
            return video && !video.paused && !video.ended && video.readyState > 2;
        """
        )
        if is_playing:
            return True
        sb.execute_script(
            f"""
            var video = document.querySelector("{selector}");
            if (video) {{
                video.muted = true;
                video.play().catch(e => console.warn("Autoplay blocked:", e));
            }}
        """
        )

        sb.wait(2)
    print("Video did not start playing in time")
    return False


def stop_video_play(sb, selector="video", timeout=15):
    start = time.time()
    sb.wait_for_element_present("css selector", selector, timeout)
    while time.time() - start < timeout:
        is_playing = sb.execute_script(
            f"""
            var video = document.querySelector("{selector}");
            return video && !video.paused && !video.ended && video.readyState > 2;
        """
        )
        if not is_playing:
            return True
        sb.execute_script(
            f"""
            var video = document.querySelector("{selector}");
            if (video) {{
                video.muted = true;
                video.pause()
                video.currentTime = 0;
            }}
        """
        )
        sb.wait(2)
    print("Video did not pause in time")
    return False


def go_to_episode_page(sb, episode_url):
    try:
        sb.wait_for_element_present(
            "css selector",
            ".episode-list .erc-playable-collection .card a[href='" + urlparse(episode_url).path + "']",
            timeout=15,
        )

        sb.click(
            ".episode-list .erc-playable-collection .card a[href='" + urlparse(episode_url).path + "']",
            by="css selector",
        )
        screenshot.take(sb)
        # accept_consent(sb)
        sb.wait_for_element_present("css selector", "iframe.video-player", timeout=15)
        screenshot.take(sb)
        sb.wait(1)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def slowdown_if_restrictions_overlay(sb: BaseCase):
    if sb.is_element_present("css selector", "#restrictionsOverlay"):
        cooldown = 30
        print(f"Restrictions overlay detected, waiting {cooldown}s")
        sb.wait(cooldown)
        slowdown_if_restrictions_overlay(sb)


def go_back_to_ep_lists_page(sb: BaseCase, season):
    try:
        if sb.is_element_clickable("css selector", 'a[data-t="show-title-link"]'):
            sb.click("a.show-title-link", by="css selector")
            print("Going back to previous page")
        else:
            sb.go_back()
        select_season_from_dropdown_list(sb, season)
        click_load_more_btn(sb)
    except Exception as e:
        sb.driver.switch_to.default_content()
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def get_series_url_from_watch_page(sb: BaseCase):
    try:
        if "/watch/" in sb.driver.current_url:
            meta_tag_el = sb.wait_for_element_present("css selector", 'meta[property="video:series"]', timeout=15)
            return meta_tag_el.get_attribute("content")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def click_see_more_episodes_from_watch_page(sb: BaseCase):
    try:
        if sb.is_element_present("css selector", 'button[data-t="see-more-episodes-btn"]'):
            sb.click('button[data-t="see-more-episodes-btn"]', by="css selector")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def close_see_more_episodes_in_watch_page(sb: BaseCase):
    try:
        if sb.is_element_present("css selector", 'button[class^="modal-portal__close-button"]'):
            sb.click('button[class^="modal-portal__close-button"]', by="css selector")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def add_new_downloaded_subtitle(key, value):
    global new_downloaded_subtitles
    if key not in new_downloaded_subtitles:
        new_downloaded_subtitles[key] = []
    new_downloaded_subtitles[key].append(value)


def get_console_logs(sb):
    logs = sb.driver.get_log("browser")
    for entry in logs:
        print(f"[{entry['level']}] {entry['message']}")


# def accept_consent(sb):
#     sb.wait(3)
#     if sb.is_element_present("css selector", "button[data-t='grant-player-anonymous-consent-btn']"):
#         sb.click("button[data-t='grant-player-anonymous-consent-btn']")
#         sb.wait(5)
#         screenshot.take(sb)
