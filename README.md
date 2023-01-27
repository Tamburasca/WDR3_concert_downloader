# WDR3 Concert Downloader

Downloads mp3 audio files from a WDR3 concert player site if this website
permits only an afterhearing option of 30 days and, hence, no download button
is available. From the address bar of your web browser copy the url of the 
site - where the concert resides - and run the code:

    $ python3 WDR3_concert_downloader/src <url> -o <file.mp3>

where e.g.

url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html

Note: if multiple mp3 media objects are available on the website provided,
files will be downloaded and named according the scheme
file.mp3, file(1).mp3, file(2).mp3, etc. in the order the objects are 
encountered in the html soup scan.

Runs with Python 3.10

Comments welcome