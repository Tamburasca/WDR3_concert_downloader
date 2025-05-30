#!/usr/bin/env python3
# coding: utf-8

"""
see for conversion from JavaScript to Python 3.13
https://github.com/PiotrDabkowski/Js2Py
"""

import requests
import re
import glob
import js2py_  # ECMA 6 support is still experimental, check for final development
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl


PATTERN = re.compile(r'"audioURL"\s?:\s?"(.*\.mp3)"')
# Javascript definitions and supplements
JS_PREFIX = "var globalObject = {};\n"
JS_SUFFIX = (
    "var firstkey = Object.keys(globalObject.gseaInlineMediaData)[0];\n"
    "globalObject.gseaInlineMediaData[firstkey];\n"
)


class TestURL(BaseModel):
    url: HttpUrl


def wdr3_scraper(
        url: str,
        file: str = "download.mp3"
) -> int:
    counter = 0
    try:
        if not file.endswith(".mp3"):
            raise NameError(file)
        download = "{0}*.mp3".format(file.rsplit(".", 1)[0])
        if glob.glob(download):
            raise FileExistsError(download)
        # verificare e tentare d'aprire url iniziale
        response = requests.get(url=TestURL(url=url).url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # extract content within script tags which matches regEx
        for script in soup.find_all('script', text=PATTERN):
            # js_dict is js2py_.base.JsObjectWrapper object, not a dict!
            js_dict = js2py_.eval_js(JS_PREFIX + script.string + JS_SUFFIX)
            mp3_url = js_dict['mediaResource']['dflt']['audioURL']
            if mp3_url:
                file_download = file if counter == 0 else "{0}({1}).mp3".format(
                    file.rsplit(".", 1)[0],
                    counter
                )
                sneak_mp3 = "https:{}".format(mp3_url)
                # apri l'oggetto mp3 e download suo contenuto binario sul file
                doc = requests.get(url=sneak_mp3)
                doc.raise_for_status()
                with open(file_download, 'wb') as f:
                    f.write(doc.content)
                print("{1} downloaded to {0} successfully".format(
                    file_download,
                    sneak_mp3)
                )
                counter += 1
        if counter == 0:
            raise RuntimeWarning
        return 0
    except NameError as e:
        print("Error: download filename '{}' is incorrect.".format(e))
    except FileExistsError as e:
        print("Error: download file '{}' exists. Exiting ...".format(e))
    except RuntimeWarning:
        print("Warning: No mp3 link found under '{}' html.".format(url))
    except Exception as e:
        print("Error: {}".format(str(e)))  # Minchia, che palle!
    return 1
