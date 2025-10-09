import copy
import json
import os
import re
import time
import traceback
from collections import defaultdict
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from seleniumbase import BaseCase

import config
import screenshot
import subtitle_processor

new_downloaded_subtitles = defaultdict(lambda: defaultdict(list))


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
    print("⏳ Loading animes list")

    list_downloaded = []
    with open(os.path.join("output", "saved_file.json"), "r") as f2:
        list_downloaded = json.load(f2)

    animes = []
    if not single_url:
        f = open("animes.json")
        animes = json.load(f)
    elif any(url in single_url for url in ["/series/", "/watch/"]):
        animes.append({"url": single_url})
    else:
        print(f"❌ Invalid Episode/Series URL: {single_url}")
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
            print("❌ Missing URL in animes.json")
            continue

        anime["lang"] = anime.get("lang") or []
        if "/series/" in anime.get("url"):
            print(f"⏳ Checking Series URL: {anime['url']}")
            anime["seasons"] = anime.get("seasons") or []
            latest_season = False
            if anime.get("seasons"):
                for s in anime.get("seasons"):
                    if s < 0:
                        latest_season = True
                        break
            if (not anime.get("seasons")) or latest_season:
                go_to_url(sb, anime.get("url"))
                if sb.is_element_present(selector='[class^="empty-state__container"]'):
                    print("❌ This series or season isn't available in your country")
                    continue

                anime["seasons"], _ = get_all_season_indexes(sb) or []
                if latest_season:
                    anime["seasons"] = [anime["seasons"][-1]] if anime["seasons"] else []

            for season in anime["seasons"]:
                handle_season(sb, anime, season, list_downloaded, force_download)
        elif "/watch/" in anime.get("url"):
            print(f"⏳ Checking epsode URL: {anime.get('url')}")
            handle_single_episode(sb, anime.get("url"), anime.get("lang"), list_downloaded, force_download)
        else:
            print(f"❌ Invalid Epsode/Series URL: {anime.get('url')}")

    with open(os.path.join("output", "latest_downloaded.txt"), "w") as f3:
        if new_downloaded_subtitles:
            print(f"--------------------------------------------------------------------------------")
            print(f"✅ New subtitles downloaded:")
            f3.write(f"New subtitles downloaded:\n")

            for series, seasons in new_downloaded_subtitles.items():
                print(f"    {series}:")
                f3.write(f"    {series}:\n")
                for season_title, episodes in seasons.items():
                    if series != season_title:
                        print(f"        {season_title}")
                        f3.write(f"        {season_title}\n")
                        for episode in episodes:
                            print(f"            {episode}")
                            f3.write(f"            {episode}\n")
                    else:
                        for episode in episodes:
                            print(f"        {episode}")
                            f3.write(f"        {episode}\n")
        else:
            print("👌 No new subtitles.")
            f3.write("No new subtitles.\n")


def handle_season(sb: BaseCase, series, season, list_downloaded, force_download=False):
    if not series.get("url") or int(season) < 1:
        return
    xv = [x for x in list_downloaded if x["url"] == series["url"] and int(x["season"]) == int(season)]
    skip_episodes = list(xv[0]["downloaded"]) if xv else list()
    if not urls_equal(sb.get_current_url(), series["url"]):
        go_to_url(sb, series["url"])

    print(f"⏳ Checking season number: {str(season)}")
    if sb.is_element_present(selector='[class^="empty-state__container"]'):
        print("❌ This series or season isn't available in your country")
        return

    season = select_season_from_dropdown_list(sb, season)
    screenshot.take(sb)
    if not season:
        return
    screenshot.take(sb)

    first_ep_url_in_series = sb.wait_for_attribute(
        attribute="href",
        selector=".episode-list a[class^='playable-card__thumbnail-wrapper']",
        by="css selector",
        timeout=30,
    ).get_attribute("href")

    go_to_url(sb, first_ep_url_in_series)
    get_episode_metadata(sb, season, first_ep_url_in_series)
    # List profile audio language
    episode_urls, season_title = get_list_of_episode_urls_in_watch_page(sb)
    screenshot.take(sb)
    if series.get("latest") and episode_urls:
        episode_urls = episode_urls[-series.get("latest") :]
    total_episodes_episodes = len(episode_urls)

    print(f"Total number of episodes in {season_title}: {str(total_episodes_episodes)}")
    open_episode_url(sb, series, season, episode_urls, skip_episodes, force_download=force_download)
    screenshot.take(sb)


def handle_single_episode(sb: BaseCase, episode_url, lang=[], list_downloaded=[], force_download=False):
    series = AttrDict()
    series.lang = lang or []

    go_to_url(sb, episode_url)
    if sb.is_element_present(selector='meta[name="prerender-status-code"][content="404"]'):
        print("❌ This series or season isn't available in your country")
        return

    series.url = get_series_url_from_watch_page(sb)
    click_see_more_episodes_from_watch_page(sb)
    _, season = get_all_season_indexes(sb)
    if sb.is_element_present(selector='[class^="empty-state__container"]'):
        print("❌ This series or season isn't available in your country")
        return

    if not season or season <= 0:
        print("❌ No seasons found")
        return

    xv = [x for x in list_downloaded if x["url"] == series["url"] and x["season"] == season]
    skip_episodes = list(xv[0]["downloaded"]) if xv else list()
    open_episode_url(
        sb,
        series,
        season,
        [episode_url],
        skip_episodes,
        suppress_download_msg=True,
        force_download=force_download,
    )


def get_all_season_indexes(sb: BaseCase) -> tuple[list, int]:
    try:
        if "/watch/" in sb.get_current_url() and not sb.is_element_present(selector=".erc-watch-more-episodes"):
            series_url = get_series_url_from_watch_page(sb)
            if not series_url:
                return [1], 1
            go_to_url(sb, series_url)

        sb.wait_for_any_of_elements_present(
            '[class^="empty-state__container"]',
            ".episode-list .erc-playable-collection",
            ".episode-list-expanded .episode-list",
        )
        if sb.is_element_present(by="css selector", selector=".season-info"):
            sb.click(selector=".season-info", by="css selector")
            sb.wait_for_element_present(by="css selector", selector="[class^='dropdown-content__children']", timeout=30)

            list_season_el = sb.find_elements(
                by="css selector",
                selector="[class^='dropdown-content__children'] div[class^='extended-option']",
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
        print(f"❌ Error: {e}")
        if config.DEBUG:
            traceback.print_exc()
        screenshot.take(sb)
        # accept_consent(sb)
    return [], 0


def click_load_more_btn(sb: BaseCase):
    try:
        while True:
            sb.wait_for_element_present(by="css selector", selector="div.erc-season-episode-list", timeout=30)

            if sb.is_element_present(by="css selector", selector="[data-t='show-more-btn']"):
                sb.click(selector="[data-t='show-more-btn']", by="css selector")
                sb.wait_for_element_present(by="css selector", selector="div.erc-season-episode-list", timeout=30)
            else:
                # sb.wait(1)
                break
    except Exception as e:
        print(f"❌ Cannot click load more, Error: {e}")
        if config.DEBUG:
            traceback.print_exc()
        return


def select_season_from_dropdown_list(sb: BaseCase, season):
    try:
        sb.wait_for_element_present(by="css selector", selector=".episode-list .erc-playable-collection", timeout=30)
        if sb.is_element_present(by="css selector", selector=".season-info"):
            if not sb.is_element_present(selector="[class^='dropdown-content__children']"):
                sb.click(selector=".season-info", by="css selector")
            sb.wait_for_element_present(by="css selector", selector="[class^='dropdown-content__children']", timeout=30)
            sb.click(
                selector="[class^='dropdown-content__children'] > div > div:nth-child(" + str(season) + ")",
                by="css selector",
            )
            sb.wait_for_element_present(by="css selector", selector=".erc-season-episode-list", timeout=30)
            return season
        else:
            if season != 1:
                print("❌ Invalid season number, fallback to season 1")
            return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if config.DEBUG:
            traceback.print_exc()
        screenshot.take(sb)
        # accept_consent(sb)
        return


def open_episode_url(
    sb: BaseCase,
    anime,
    season,
    episodes_urls=[],
    skip_episodes=[],
    suppress_download_msg=False,
    force_download=False,
):
    for index, episode_url in enumerate(episodes_urls):

        languages_to_download = []
        languages_to_skip = (
            next((ep["lang"] for ep in skip_episodes if ep["url"] == episode_url), []) if not force_download else []
        )
        for lang in anime["lang"]:
            if not force_download and any(ep["url"] == episode_url and lang in ep["lang"] for ep in skip_episodes):
                continue
            else:
                languages_to_download.append(lang)

        if len(anime["lang"]) > 0 and len(languages_to_download) == 0:
            continue
        if not suppress_download_msg:
            print(f"⏳ Checking episode URL: {str(episode_url)}")
        if sb.get_current_url() != episode_url:
            go_to_url(sb, episode_url)
            sb.wait_for_ready_state_complete()

        episode_metadata = get_episode_metadata(sb, season, episode_url)
        if episode_metadata is None:
            continue

        if len(episode_metadata["playService"]["subtitles"]) == 0:
            print("No subtitles found!")
            log_downloaded_episode(anime, season, skip_episodes)
            continue
        downloaded_subtitles = save_episode_subtitles(sb, episode_metadata, languages_to_download, languages_to_skip)
        downloaded_subtitles_langs = sorted(set(d["lang"] for d in downloaded_subtitles))

        if episode_metadata["playService"]["versions"]:
            ep_id_list = [v["guid"] for v in episode_metadata["playService"]["versions"]]
            all_ep_urls_from_all_audio = [re.sub(r"(?<=/watch/)[^/]+", ep_id, episode_url) for ep_id in ep_id_list]
        else:
            all_ep_urls_from_all_audio = [episode_url]
        skip_episodes = append_lang_to_skip_urls(skip_episodes, all_ep_urls_from_all_audio, downloaded_subtitles_langs)
        log_downloaded_episode(anime, season, skip_episodes)
        if len(downloaded_subtitles) > 0:
            print("✅ Downloaded new subtiles: " + ", ".join(downloaded_subtitles_langs))
        if len(languages_to_download) > 0 and len(languages_to_download) != len(downloaded_subtitles_langs):
            print(
                "😭 Missing subtitles: " + ", ".join(d for d in languages_to_download if d not in downloaded_subtitles)
            )


def wait_for_metadata(sb: BaseCase, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            metadata = json.loads(sb.execute_script("return JSON.stringify(self.v1config.media)"))
            if metadata:
                return metadata
        except:
            sb.wait(0.1)
            continue
        sb.wait(0.1)
    print("❌ metadata take forever to get")
    return


def get_episode_metadata(sb: BaseCase, season, episode_url, attempts=3):
    """This also go to origin audio episode URL"""
    if attempts == 0:
        print("❌ Error getting episode metadata")
        return
    try:
        iframe = sb.wait_for_element_present(by="css selector", selector="iframe.video-player", timeout=30)
        sb.scroll_to_element(selector="iframe.video-player", by="css selector")
        sb.driver.switch_to.frame(iframe)
        screenshot.take(sb)
        metadata = wait_for_metadata(sb)
        if metadata:
            screenshot.take(sb)
            slowdown_if_restrictions_overlay(sb)
            screenshot.take(sb)
            sb.driver.switch_to.default_content()

            if config.DEBUG and metadata:
                with open("mediainfo.json", "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            original_audio = next((v for v in metadata["playService"]["versions"] if v.get("original") is True), None)
            current_ep_id = get_crunchyroll_id(sb.get_current_url())
            if original_audio and "guid" in original_audio and current_ep_id != original_audio["guid"]:
                episode_url = f'https://www.crunchyroll.com/watch/{original_audio["guid"]}'
                print(f"↩️ Switching to the original audio language: {original_audio["audio_locale"]}")
                sb.scroll_to_top()
                go_to_url(sb, episode_url)
                return get_episode_metadata(sb, season, episode_url, attempts)
            else:
                sb.scroll_to_top()
                return metadata
        screenshot.take(sb)
        sb.driver.switch_to.default_content()
    except:
        if config.DEBUG:
            traceback.print_exc()
        print("❌ Error getting episode metadata, Retrying...")
        if not slowdown_if_restrictions_overlay(sb):
            sb.driver.switch_to.default_content()
            sb.refresh()
        sb.driver.switch_to.default_content()
        return get_episode_metadata(sb, season, episode_url, attempts - 1)


def safe_filename(name, replacement="_", max_length=255):
    # Replace invalid characters with the replacement character
    safe = re.sub(r'[\\/:*?"<>|]', replacement, name).strip()
    return safe[:max_length]


def save_episode_subtitles(sb: BaseCase, tvshow_info, lang_to_download=[], downloaded_language=[]):
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
        sb.save_file_as(
            file_url=list_subtitle_from_crunchyroll[subtitle]["url"],
            new_file_name=save_filename,
            destination_folder=save_folder,
        )
        output = os.path.join(save_folder, save_filename)

        subtitles.append(
            {
                "lang": list_subtitle_from_crunchyroll[subtitle]["language"],
                "url": output,
            }
        )
        if list_subtitle_from_crunchyroll[subtitle]["language"] == "vi-VN":
            subtitle_processor.clean_subtitle(output, output, is_replace_font=True)
        else:
            subtitle_processor.clean_subtitle(output, output, is_replace_font=False)
        add_new_downloaded_subtitle(
            tvshow_info["metadata"]["series_title"],
            season_title,
            f"E{tvshow_info["metadata"]["display_episode_number"]} ({list_subtitle_from_crunchyroll[subtitle]["language"]}): {tvshow_info["metadata"]["title"]}",
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


def append_lang_to_skip_urls(skip_episodes, updated_episode_urls, episode_langs):
    langs = list(set(episode_langs))  # prepare language list once

    # Loop over skip_episodes and update languages if URL matches
    for downloaded in skip_episodes:
        for ep_url in updated_episode_urls[:]:  # iterate over a copy
            if downloaded["url"] == ep_url:
                # Merge languages without duplicates
                downloaded["lang"] = list(set(downloaded["lang"]) | set(episode_langs))
                # Remove matched URL from updated_episode_urls
                updated_episode_urls.remove(ep_url)

    # Add any remaining URLs as new entries
    for ep_url in updated_episode_urls:
        skip_episodes.append({"url": ep_url, "lang": langs})

    return skip_episodes


def get_list_of_episode_urls_in_watch_page(sb: BaseCase):
    click_see_more_episodes_from_watch_page(sb)
    print("Getting list of episode")
    sb.wait_for_element_present(by="css selector", selector=".current-media-wrapper", timeout=30)
    has_ep_list_elm = sb.is_element_present(by="css selector", selector=".episode-list")
    full_url = sb.get_current_url()
    parsed = urlparse(full_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    season_title = next(
        (
            sb.get_text_content(selector=sel)
            for sel in [
                '.season-info [class^="select-trigger__title"]',
                ".episode-list-select h4",
                ".erc-episode-list-modal h4",
            ]
            if sb.is_element_present(selector=sel)
        ),
        "",
    )

    if has_ep_list_elm:
        ep_elements = sb.find_elements(
            by="css selector",
            selector=".episode-list a[class^='playable-card-mini-static__link'], "
            ".episode-list a[class^='playable-card__thumbnail-wrapper']",
        )
        return [
            urljoin(base_url, el.get_attribute("href")) for el in ep_elements if el.get_attribute("href").strip()
        ], season_title
    return [parsed.path], season_title


def wait_for_video_to_play(sb: BaseCase, selector="video", timeout=30):
    start = time.time()
    sb.wait_for_element_present(by="css selector", selector=selector, timeout=timeout)
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
    print("❌ Video did not start playing in time")
    return False


def stop_video_play(sb: BaseCase, selector="video", timeout=30):
    start = time.time()
    sb.wait_for_element_present(by="css selector", selector=selector, timeout=timeout)
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
        sb.wait(1)
    print("❌ Video did not pause in time")
    return False


def slowdown_if_restrictions_overlay(sb: BaseCase):
    if sb.is_element_present(by="css selector", selector="#restrictionsOverlay"):
        cooldown = 60
        print(f"⚠️ Restrictions overlay detected, waiting {cooldown}s")
        screenshot.take(sb)
        sb.wait(cooldown)
        elements = sb.find_elements(by="css selector", selector="#restrictionsOverlay div")
        matched_el = next((el for el in elements if "TRY AGAIN" in el.text), None)
        if matched_el:
            matched_el.click()
            return True
    return False


def get_series_url_from_watch_page(sb: BaseCase):
    try:
        if "/watch/" in sb.get_current_url():
            meta_tag_el = sb.wait_for_element_present(
                by="css selector", selector='meta[property="video:series"]', timeout=30
            )
            return meta_tag_el.get_attribute("content")
    except Exception as e:
        print(f"❌ Error: {e}")
        if config.DEBUG:
            traceback.print_exc()
        screenshot.take(sb)


def get_crunchyroll_id(url: str) -> str | None:
    path_parts = urlparse(url).path.strip("/").split("/")

    if "watch" in path_parts:
        idx = path_parts.index("watch")
        if idx + 1 < len(path_parts):
            return path_parts[idx + 1]
    return None


def click_see_more_episodes_from_watch_page(sb: BaseCase):
    """Still load listed of episodes with the same audio language with user profile"""
    try:
        if not sb.is_element_present(selector=".erc-watch-more-episodes"):
            return

        sb.wait_for_ready_state_complete()
        sb.wait_for_any_of_elements_present(
            "button.see-all-button", ".erc-episode-list-expanded.episode-list-expanded.state-visible"
        )
        if sb.is_element_clickable(selector="button.see-all-button", by="css selector"):
            try:
                sb.click(selector="button.see-all-button", by="css selector")
                sb.wait_for_element_present(by="css selector", selector=".episode-list", timeout=30)
            except:
                sb.wait(0)

    except Exception as e:
        print(f"❌ Error: {e}")
        if config.DEBUG:
            traceback.print_exc()
        screenshot.take(sb)


def add_new_downloaded_subtitle(series, season_title, episode):
    global new_downloaded_subtitles
    new_downloaded_subtitles[series][season_title].append(episode)


def go_to_url(sb: BaseCase, url: str):
    sb.execute_script(f'window.location.href = "{url}"')
    sb.wait(0.1)
    sb.wait_for_ready_state_complete()


def get_console_logs(sb: BaseCase):
    logs = sb.driver.get_log("browser")
    for entry in logs:
        print(f"[{entry['level']}] {entry['message']}")


def urls_equal(url1, url2):
    p1 = urlparse(url1)
    p2 = urlparse(url2)

    # Normalize path by stripping trailing "/"
    path1 = p1.path.rstrip("/")
    path2 = p2.path.rstrip("/")

    return (
        p1.scheme == p2.scheme
        and p1.netloc == p2.netloc
        and path1 == path2
        and p1.query == p2.query
        and p1.fragment == p2.fragment
    )


# def accept_consent(sb):
#     sb.wait(3)
#     if sb.is_element_present(by="css selector", selector="button[data-t='grant-player-anonymous-consent-btn']"):
#         sb.click(selector="button[data-t='grant-player-anonymous-consent-btn']")
#         sb.wait(5)
#         screenshot.take(sb)
