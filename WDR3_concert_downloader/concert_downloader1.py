#!/usr/bin/env python3

import re

import requests
from bs4 import BeautifulSoup

PATTERN = re.compile(r'"audioURL"\s?:\s?"(.*\.mp3)"')


def wdr3_scraper(
        url: str,
        filepath: str = "download.mp3"
) -> int:
    """
       download mp3(s)
       :param url:
       :param filepath:
       :return: exit code
       """
    counter = 0
    try:
        # verificare e tentare d'aprire url iniziale
        r = requests.get(url=url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # extract content within script tags which matches regEx
        for script in soup.find_all('script', text=PATTERN):
            mp3_url = re.findall(PATTERN, script.text)

            if mp3_url:
                file_download = \
                    filepath if counter == 0 else "{0}_{1}.mp3".format(
                        filepath.rsplit(".", 1)[0],
                        counter
                    )
                sneak_mp3 = "https:{}".format(mp3_url[0])
                # apri l'oggetto mp3 e download suo contenuto binario sul file
                mp3 = requests.get(url=sneak_mp3)
                mp3.raise_for_status()
                with open(file_download, 'wb') as f:
                    f.write(mp3.content)
                print("{1} downloaded to {0} successfully".format(
                    file_download,
                    sneak_mp3
                ))
                counter += 1
        if counter == 0:
            raise RuntimeWarning

        return 0

    except RuntimeWarning:
        print("Warning: No mp3 link found under '{}' html.".format(url))
    except Exception as e:
        print("Error: {}".format(str(e)))  # Minchia, che palle!

    return 1
