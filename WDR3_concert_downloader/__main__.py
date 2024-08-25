#!/usr/bin/env python3

"""
Downloads mp3 files from a site where the WDR3 concert player is located if
there's only an afterhearing option of 30 days and, hence, no download button
available. Copy the url of the site, where the concert resides and run the code:

$ python3 WDR3_concert_downloader [-h] [-o <file>.mp3] <url>

where e.g.
url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html
Note: if there are multiple mp3 media objects available on the provided website,
the files downloaded are named in following order:
file.mp3, file(1).mp3, file(2).mp3, etc. according to the objects encountered in
the html soup scan.
"""

from argparse import ArgumentParser
from sys import exit
from concert_downloader1 import wdr3_scraper

"""
version history:
2024/08/18 - Ralf A. Timmermann <rtimmermann@astro.uni-bonn.de>
- version 2.0.0
    * scrape script for audioURL and extract via regExp
2024/08/25 - Ralf A. Timmermann <rtimmermann@astro.uni-bonn.de>
- version 2.1.0
    * exit, if download file exists
"""

__author__ = "Dr. Ralf Antonius Timmermann"
__copyright__ = ("Copyright (c) 2024, Dr. Ralf Antonius Timmermann "
                 "All rights reserved.")
__credits__ = []
__license__ = "BSD 3-Clause"
__version__ = "2.1.0"
__maintainer__ = "Dr. Ralf Antonius Timmermann"
__email__ = "rtimmermann@gmx.de"
__status__ = "Prod"


def main():
    parser = ArgumentParser(
        description="Downloads audio mp3 files from WDR3 concert web sites.")
    parser.add_argument(
        '-o',
        '--output',
        default='download.mp3',
        nargs='?',
        help='Output file (.mp3) (default: download.mp3)')
    parser.add_argument('url',
                        help='URL of web site where concert player resides')
    exit(
        wdr3_scraper(
            url=parser.parse_args().url,
            file=parser.parse_args().output
        )
    )


if __name__ == '__main__':
    main()
