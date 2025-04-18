# Crunchyroll-sub-downloader

Crunchyroll-sub-downloader is a Python script that downloads subtitles for anime from Crunchyroll using selenium.

## Installation

### Requirements

- Python >= 3.12
- pip
- git

### Installation

```bash
git clone https://github.com/boydaihungst/crunchyroll-sub-downloader.git
cd crunchyroll-sub-downloader
pip install -r requirements.txt
cp credentials.json.example credentials.json
```

## Usage

- Add crunchyroll premium account and password in `credentials.json` file.
- Change `seasons`, `langs`, `url` in `animes.json`, then run the following command:
- You can also download subtitles for specific languages and season numbers by adding them to the `lang` and `seasons` in animes.json. If not specified, the script will download subtitles for all languages and all seasons. Season numbers start from 1 and go up to n, as listed in the season drop-down menu on the Crunchyroll website.

  ```json
    {
      "lang": [ --> List of languages to download subtitles for (Optional)
        "vi-VN",
        "en-US"
      ],
      "seasons": [ --> List of season numbers to download subtitles for (Optional)
        1,2
      ],
      "url": "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark" -> URL of the anime (Required)
    },
    {
      "seasons": [ --> Only download the first season, and all languages
        1
      ],
      "url": "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark" -> URL of the anime (Required)
    },
    { --> Download all languages and seasons
      "url": "https://www.crunchyroll.com/series/GVDHX85EQ/catch-me-at-the-ballpark" -> URL of the anime (Required)
    },
  ```

```bash
python3 main.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
