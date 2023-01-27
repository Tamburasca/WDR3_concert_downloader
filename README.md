# WDR3 Concert Downloader

Downloads audio mp3 files from a WDR3 concert player site if this website
exhibits only an afterhearing option of 30 days and, hence, no download button
is available. Copy the url of the site,
where the concert resides, and run the code:

    $ python3 WDR3_concert_downloader/src <url> -o <file.mp3>
where e.g.
url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html

Note: if multiple mp3 media objects are available on the website provided,
files will be downloaded and named in the following order:
file.mp3, file(1).mp3, file(2).mp3, etc. according to the objects encountered in
the html soup scan.

Runs with Python 3.10

Contact: Dr. Ralf Antonius Timmermann, rtimmermann@astro.uni-bonn.de