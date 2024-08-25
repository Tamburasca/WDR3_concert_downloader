import requests
from bs4 import BeautifulSoup
import re
from pydantic import BaseModel, HttpUrl
import os.path


class TestURL(BaseModel):
    url: HttpUrl


def wdr3_scraper(
        url: str,
        file: str = "download.mp3"
) -> int:
    pattern = re.compile(r'"audioURL" : "(.*)"')
    counter = 0
    try:
        if not file.endswith(".mp3"):
            raise NameError(file)
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
                    raise FileExistsError(file_download)
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
    except NameError as e:
        print("Error: download filename '{}' is incorrect.".format(e))
    except FileExistsError as e:
        print("Error: download file '{}' exists. Exiting ...".format(e))
    except Exception as e:
        print("Occurred error: {}".format(str(e)))  # Bih, chi camurrìa!
    return 1
