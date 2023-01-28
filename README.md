# WDR3 Concert Downloader

Downloads audio mp3 files (@256 kbit/s) 
from a WDR3 concert player website, if the concert 
is made available in the media library for re-listening over 
30 days after its broadcast, hence, no download button
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

Note: this downloader is not supported by any broadcasting organization, thus is 
inofficial!

I found no way to downgrade the bitrate of the mp3 audio file to a smaller 
size without having to install **ffmpeg** or an add-on for **sox** locally. 
Suggestions welcome!