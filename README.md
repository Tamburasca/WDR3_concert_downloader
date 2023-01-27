# WDR3 Concert Downloader

Downloads audio mp3 files from a WDR3 concert player website, if the concert 
is available for re-listening for 30 days in the media library the day 
after the broadcast, hence, no download button
is provided. From the address bar of your web browser copy the url of the 
website, where the concert resides and then execute the following command:

    $ python3 WDR3_concert_downloader/src <url> -o <file.mp3>

where e.g.

url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html

Note: if multiple mp3 media objects are available on the website provided,
files will be downloaded and named according the scheme
file.mp3, file(1).mp3, file(2).mp3, etc. in the order the objects are 
encountered in the html soup scan.

Runs with Python 3.10

Comments welcome