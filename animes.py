import json
import os
import re
import time
import traceback
from urllib.parse import urljoin, urlparse

import screenshot
import subtitle_processor

new_downloaded_subtitles = {}


def start_download_anime(sb):
    print("Loading animes list")
    f = open("animes.json")
    f2 = open(os.path.join("output", "saved_file.json"))
    animes = json.load(f)
    list_downloaded = json.load(f2)
    for anime in animes:
        print(f"--------------------------------------------------------------------------------")
        print(f"Checking anime URL: {anime['url']}")
        seasons = anime.get("seasons") or get_all_season_indexes(sb, anime.get("url")) or []
        anime["lang"] = anime.get("lang") or []
        for season in seasons:
            handle_season(sb, anime, season, list_downloaded)
    if new_downloaded_subtitles:
        print(f"New subtitles downloaded:")
        for key, value in new_downloaded_subtitles.items():
            print(f"    {key}:")
            for v in value:
                print(f"        {v}")
    else:
        print("No new subtitles.")


def handle_season(sb, series, season, list_downloaded):
    if not series.get("url") or int(season) < 1:
        return
    xv = [x for x in list_downloaded if x["url"] == series["url"] and x["season"] == season]
    skip_episodes = list(xv[0]["downloaded"]) if xv else list()
    sb.open(series["url"])

    try:
        print(f"Checking season number: {str(season)}")
        select_season_from_dropdown_list(sb, season)
        click_load_more_btn(sb)
        episode_urls = get_list_of_episode_urls(sb)
        total_episodes_episodes = len(episode_urls)

        print(f"Total number of episodes in season {season}: {str(total_episodes_episodes)}")
        open_episode_url(sb, series, season, episode_urls, skip_episodes)
    except:
        traceback.print_exc()


def get_all_season_indexes(sb, anime_url):
    try:
        if not anime_url:
            return []
        sb.open(anime_url)
        sb.wait_for_element("css selector", ".episode-list .erc-playable-collection", timeout=15)

        if sb.is_element_present("css selector", ".season-info > h4 > span"):
            sb.click(".season-info", by="css selector")
            sb.wait_for_element("css selector", "[class^='dropdown-content__children']", timeout=15)
            season_count = len(
                sb.driver.find_elements(
                    "css selector", "[class^='dropdown-content__children'] div[class^='extended-option']"
                )
            )
            return list(range(1, season_count + 1))
        else:
            return [1]
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)
        # accept_consent(sb)
    return []


def click_load_more_btn(sb):
    try:
        while True:
            sb.wait_for_element("css selector", "div.erc-season-episode-list", timeout=15)

            if sb.is_element_present("css selector", "[data-t='show-more-btn']"):
                sb.click("[data-t='show-more-btn']", by="css selector")
                # sb.wait(3)
                sb.wait_for_element("css selector", "div.erc-season-episode-list", timeout=15)
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
        sb.wait_for_element("css selector", ".episode-list .erc-playable-collection", timeout=15)
        if sb.is_element_present("css selector", ".season-info > h4 > span"):
            sb.click(".season-info", by="css selector")
            sb.wait_for_element("css selector", "[class^='dropdown-content__children']", timeout=15)
            sb.click(
                "[class^='dropdown-content__children'] > div > div:nth-child(" + str(season) + ")",
                by="css selector",
            )
            sb.wait_for_element("css selector", ".erc-season-episode-list", timeout=15)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)
        # accept_consent(sb)
        return


def open_episode_url(sb, anime, season, episodes_urls=[], skip_episodes=[]):
    for episode_url in episodes_urls:
        languages_to_download = []
        languages_to_skip = [ep["lang"] for ep in skip_episodes if ep["url"] == episode_url]
        for lang in anime["lang"]:
            if any(ep["url"] == episode_url and lang in ep["lang"] for ep in skip_episodes):
                continue
            else:
                languages_to_download.append(lang)

        if len(anime["lang"]) > 0 and len(languages_to_download) == 0:
            continue
        print(f"Checking episode URL: {str(episode_url)}")
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
        append_lang_to_skip_urls(skip_episodes, episode_url, downloaded_subtitles_langs)
        log_downloaded_episode(anime, season, skip_episodes)
        if len(downloaded_subtitles) > 0:
            print("Downloaded new subtiles: " + ", ".join(downloaded_subtitles_langs))
        if len(languages_to_download) > 0 and len(languages_to_download) != len(downloaded_subtitles_langs):
            print("Missing subtitles: " + ", ".join(d for d in languages_to_download if d not in downloaded_subtitles))
        go_back_to_ep_lists_page(sb, season)


def get_episode_metadata(sb, season, episode_url, attempts=3):
    if attempts == 0:
        return
    try:
        sb.driver.uc_switch_to_frame("iframe")
        sb.wait_for_element("css selector", "video", timeout=15)

        if wait_for_video_to_play(sb, "video", timeout=15):
            screenshot.take(sb)
            return json.loads(sb.execute_script("return JSON.stringify(self.v1config.media)"))
        screenshot.take(sb)
    except:
        print("Error getting episode metadata")
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
            downloaded["lang"] = list(set(downloaded["lang"] + episode_langs))
            return

    # If not found, add new entry
    skip_episodes.append({"url": episode_url, "lang": episode_langs})


def get_list_of_episode_urls(sb):
    print("Getting list of episode")
    element = sb.wait_for_element("css selector", ".episode-list .erc-playable-collection", timeout=15)
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


def wait_for_video_to_play(sb, selector="video", timeout=15):
    start = time.time()
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
        sb.wait(1)
    print("Video did not start playing in time")
    return False


def go_to_episode_page(sb, episode_url):
    try:
        sb.wait_for_element(
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
        sb.wait_for_element("css selector", "iframe.video-player", timeout=15)
        screenshot.take(sb)
        sb.wait(1)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def slowdown_if_restrictions_overlay(sb):
    if sb.is_element_present("css selector", "#restrictionsOverlay"):
        cooldown = 60
        print(f"Restrictions overlay detected, waiting {cooldown}s")
        sb.wait(cooldown)


def go_back_to_ep_lists_page(sb, season):
    try:
        sb.go_back()
        select_season_from_dropdown_list(sb, season)
        click_load_more_btn(sb)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        screenshot.take(sb)


def add_new_downloaded_subtitle(key, value):
    global new_downloaded_subtitles
    if key not in new_downloaded_subtitles:
        new_downloaded_subtitles[key] = []
    new_downloaded_subtitles[key].append(value)


# def accept_consent(sb):
#     sb.wait(3)
#     if sb.is_element_present("css selector", "button[data-t='grant-player-anonymous-consent-btn']"):
#         sb.click("button[data-t='grant-player-anonymous-consent-btn']")
#         sb.wait(5)
#         screenshot.take(sb)
