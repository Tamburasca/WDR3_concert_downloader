import requests
from bs4 import BeautifulSoup
import json
from pydantic import BaseModel, HttpUrl


class TestURL(BaseModel):
    url: HttpUrl


def wdr3_scraper(url: str, file: str) -> int:
    counter = 0
    try:
        if not file.endswith(".mp3"):
            raise NameError
        # verificare ed tentare d'aprire url iniziale
        response = requests.get(url=TestURL(url=url).url)
        soup = BeautifulSoup(response.text, "html.parser")
        for value in soup.find_all('a'):
            data_ext = value.get('data-extension')
            if data_ext:
                sneak = json.loads(data_ext)['mediaObj']['url']
                # apri ogni javascript media object e taglia non-JSON sui due lati
                res = requests.get(url=sneak).text
                s = json.loads(
                    res.lstrip(
                        "$mediaObject.jsonpHelper.storeAndPlay("
                    ).rstrip(");")
                )
                mp3_url = "https:{}".format(
                    s['mediaResource']['dflt']['audioURL']
                )
                # apri mp3 object e download binary content sul file
                doc = requests.get(url=mp3_url)
                file_download = file if counter == 0 else "{0}({1}).mp3".format(
                    file.rsplit(".", 1)[0],
                    counter
                )
                with open(file_download, 'wb') as f:
                    f.write(doc.content)
                print("{1} downloaded to {0} successfully".format(file_download,
                                                                  mp3_url))
                counter += 1

        return 0

    except NameError:
        print("Error: filename '{}' is incorrect.".format(file))
    except Exception as e:
        print("Occurred error: {}".format(str(e)))  # Bih, chi camurrìa!

    return 1
