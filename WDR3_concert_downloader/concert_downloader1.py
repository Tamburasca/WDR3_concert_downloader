import requests
from bs4 import BeautifulSoup
import re
from pydantic import BaseModel, HttpUrl
import os.path


class TestURL(BaseModel):
    url: HttpUrl


class Error(Exception):
    pass


class FileExistsErr(Error):
    def __init__(self, msg: str):
        self.msg = msg


def wdr3_scraper(
        url: str,
        file: str
) -> int:
    pattern = re.compile(r'"audioURL" : "(.*)"')
    counter = 0
    try:
        if not file.endswith(".mp3"):
            raise NameError
        # verificare e tentare d'aprire url iniziale
        response = requests.get(url=TestURL(url=url).url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for value in soup.find_all('script', text=pattern):
            mp3_url = re.findall(pattern, value.text)
            if mp3_url:
                file_download = file if counter == 0 else "{0}({1}).mp3".format(
                    file.rsplit(".", 1)[0],
                    counter
                )
                if os.path.isfile(file_download):
                    raise FileExistsErr(file_download)
                sneak_mp3 = "https:{}".format(mp3_url[0])
                # apri l'oggetto mp3 e download il binary content sul file
                doc = requests.get(url=sneak_mp3)
                doc.raise_for_status()
                with open(file_download, 'wb') as f:
                    f.write(doc.content)
                print("{1} downloaded to {0} successfully".format(
                    file_download,
                    sneak_mp3)
                )
                counter += 1
        return 0
    except NameError:
        print("Error: filename '{}' is incorrect.".format(file))
    except FileExistsErr as e:
        print("Error: filename '{}' already exists. Exiting ...".format(e.msg))
    except Exception as e:
        print("Occurred error: {}".format(str(e)))  # Bih, chi camurrìa!
    return 1
