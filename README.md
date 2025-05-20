# Crunchyroll-sub-downloader

<!--toc:start-->

- [Crunchyroll-sub-downloader](#crunchyroll-sub-downloader)
  - [Installation](#installation)
    - [Requirements](#requirements)
    - [Clone the repository](#clone-the-repository)
    - [Setup python environment for Windows](#setup-python-environment-for-windows)
    - [Setup python environment for Unix-based systems](#setup-python-environment-for-unix-based-systems)
  - [Usage](#usage)
    - [Batch download using command line arguments](#batch-download-using-command-line-arguments)
    - [Batch download using only animes.json file](#batch-download-using-only-animesjson-file)
    - [Troubleshooting](#troubleshooting)
  - [License](#license)
  <!--toc:end-->

Crunchyroll-sub-downloader is a Python script that downloads subtitles for anime from Crunchyroll using selenium.

## Installation

### Requirements

- Python >= 3.12
- pip
- git

### Clone the repository

```bash
git clone https://github.com/boydaihungst/crunchyroll-sub-downloader.git
cd crunchyroll-sub-downloader
pip install -r requirements.txt
cp credentials.json.example credentials.json
```

### Setup python environment for Windows

Step 1: Install [Python](https://www.python.org/downloads/) and add it to the `PATH` environment variable.

Step 2: Create the Virtual Environment in folder `crunchyroll-sub-downloader`: `python -m venv .venv`

Step 3: Activate the Virtual Environment (rerun this step every time you open a new terminal):

```bash
# window cmd
.venv\Scripts\activate.bat
# or
# window powershell
Set-ExecutionPolicy Unrestricted -Scope Process
.venv\Scripts\Activate.ps1
```

Step 4: Install python libraies:
`pip install -r requirements.txt`

### Setup python environment for Unix-based systems

Step 1: Install Python, using your pakcage manager and add it to the `PATH` environment variable.
For example, on Ubuntu:

```bash
sudo apt install python3.12
```

Step 2: Create the Virtual Environment in folder `crunchyroll-sub-downloader` : `python -m venv .venv`

Step 3: Activate the Virtual Environment (rerun this step every time you open a new terminal):

```bash
# for fish shell
. .venv/bin/activate.fish
# bash shell
. .venv/bin/activate
```

## Usage

### Batch download using command line arguments

- Add crunchyroll premium account and password in `credentials.json` file.

> [!IMPORTANT]
> All of the arguments are optional even the `url` argument.
> These `-l --lang -s --season -L --latest` arguments will override the corresponding arguments in `animes.json` file.

```bash
usage: main.py [url] [-h] [-l en-US vi-VN ...] [-s -1 1 2 ...] [-L NUMBER] [-f]

Crunchyroll subtitles downloader

positional arguments:
  url                   Crunchyroll episode or series URL. If not specified, will download subtitles for all animes in animes.json file.

options:
  -h, --help            show this help message and exit
  -l, --lang [LANG ...]
                        List of languages to download subtitles for. E.g: -l vi-VN en-US.
                        If using with "animes.json" file, it will override the "lang" specified in animes.json.
                        If using with "url" argument:
                            It will download subtitles for specified languages.
                            If not specified, will download subtitles for all languages.

                        Example:
                            -l vi-VN en-US    will download subtitles for languages vi-VN and en-US. Override all the "lang" specified in animes.json.

  -s, --season [SEASON ...]
                        List of seasons number to download subtitles for.
                        If using with "animes.json" file, it will override the "seasons" specified in animes.json.
                        If using with "url" argument:
                            It will download subtitles for specified seasons.
                            If not specified, will download subtitles for all seasons.
                        Will be ignored for episode URL.

                        Example:
                            -s 1 2   will download subtitles for seasons 1 and 2.
                            -s -1    will download subtitles for the latest season.

  -L, --latest LATEST
                        Number of latest/newest episodes to download subtitles for.
                        If using with "animes.json" file, it will override the "latest" specified in animes.json.
                        If using with "url" argument:
                            It will download subtitles for specified number of latest/newest episodes.
                        Will be ignored for episode URL.

                        Examples:
                            -L 3         Download subtitles for the latest 3 episodes of all seasons.
                            -L 3 -s 1 2  Download subtitles for the latest 3 episodes of seasons 1 and 2.
                            -L 1 -s -1   Download subtitles for only the newest episode of the newest season.

  -f, --force           Force to download even if the subtitles is already downloaded
```

For example:

- Download only languages `vi-VN` and `en-US` and seasons `1` and `2`:

  ```bash
  python3 main.py "https://www.crunchyroll.com/series/GDKHZEJ0K/solo-leveling" -l vi-VN en-US -s 1 2
  ```

- Download only latest seasons:

  ```bash
  python3 main.py "https://www.crunchyroll.com/series/GDKHZEJ0K/solo-leveling" -l vi-VN en-US -s -1
  ```

- Download only languages `vi-VN` and `en-US` for the episode:

  ```bash
  python3 main.py "https://www.crunchyroll.com/watch/G8WU7V02K/way-of-the-flash" -l vi-VN en-US
  ```

### Batch download using only animes.json file

- Add crunchyroll premium account and password in `credentials.json` file.
- Change `seasons`, `langs`, `url` in `animes.json`, then run the command below.
- You can also download subtitles for specific languages, season numbers and the n number of latest episodes by adding them to the `lang`, `seasons` and `lastest` in animes.json.

  - The `url` could be either the anime URL (`/series/`) or the episode URL (`/watch/`). For the episode `seasons` are not needed and will be ignored.
  - Season numbers start from 1 and go up to n, as listed in the season drop-down menu on the Crunchyroll website. Season numbers can be set to `-1` to get the latest season.
  - If `season` and `lang` are not specified, it will download subtitles for all seasons and languages.

  - Get only the latest n number of an episode by setting `latest` to `n` number in animes.json. `"latest" = 1` and `"seasons" = [-1]` will download subtitles for the newest episode of the latest season.

- Some popular language codes:

  - `"vi-VN", "en-US", "th-TH", "id-ID", "ms-MY", "ja-JP", "ru-RU", "pt-BR", "it-IT", "fr-FR", "es-ES", "es-419", "de-DE", "ar-SA"`
  - If you want to download subtitles for a language that is not listed, you can get rid of `lang` in animes.json to download subtitles for all languages, so you can get the language code.

- Structure of animes.josn file :

  ```json
  [
    "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark", --> URL of the anime. This will download subtitles for all languages and seasons.
    "https://www.crunchyroll.com/watch/G8WU7V02K/way-of-the-flash", --> URL of the episode. This will download subtitles for a single languages and seasons.

    { --> Download only Vietnamese and English subtitles for all seasons
      "lang": [ --> List of languages to download subtitles for (Optional).
        "vi-VN",
        "en-US"
      ],
      "url": "https://www.crunchyroll.com/watch/G8WU7V02K/way-of-the-flash" -> URL of the episode (Required)
    },

    {
      "lang": [ --> List of languages to download subtitles for (Optional). Work with both anime and episode URL
        "vi-VN",
        "en-US"
      ],
      "seasons": [ --> List of season numbers to download subtitles for (Optional). Only work with anime URL.
        1,2 --> -1 mean latest season
      ],
      "latest": 1, --> latest n number of episodes (Optional). Only work with anime URL
      "url": "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark" -> URL of the anime (Required)
    },

    {  --> Only download the first season, and all languages
      "seasons": [
        1
      ],
      "url": "https://www.crunchyroll.com/series/GRDV0019R/jujutsu-kaisen"
    },

    {  --> Only download the newest episode of the latest season, and all languages
      "seasons": [ --> -1 means the latest season
        -1
      ],
      "latest": 1,
      "url": "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark"
    },

    { --> Only download the latest 3 episodes of the all seasons and all languages
      "latest": 3,
      "url": "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark"
    }
  ]
  ```

After editing the `animes.json` file, run command:

- Using default arguments in `animes.json` file:

  ```bash
    # Get all episodes of all seasons for all languages
    python3 main.py
  ```

- Download using `animes.json` file, but override the `seasons`, `lang`, `latest`:

  ```bash
  # Get only the newest episode of the latest season for languages vi-VN and en-US
  python3 main.py -l vi-VN en-US -s -1 -L 1

  # Get only the newest episode of the latest season for all languages
  python3 main.py -s -1 -L 1

  # Get only the newest episode of the season 1 and season 2 for all languages
  python3 main.py -s 1 2 -L 1

  # Get only the the last 3 episodes of all seasons for all languages
  python3 main.py -L 3
  ```

### Troubleshooting

> [!IMPORTANT]
> Crunchyroll has limited the number of devices that can access their website for each account. You should deactivate other devices if encountered with the error "Too many devices". Follow this link: https://www.crunchyroll.com/account/devices

If you encounter any issues, please add `DEBUG=true` to the start of the command to get the screenshot of the browser,then open an issue with output log and the screenshots attached (in `screenshots` folder). There could be a screenshot of login screen which you should remove before sending.

```bash
DEBUG=true python3 main.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
