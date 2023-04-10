# WDR3 Concert Downloader

Downloads audio mp3 files (@256 kbit/s) 
from a WDR3 concert player website, if the concert 
is made available in the media library for a re-listening over a
30-day period after its broadcast, hence, no download button
is dispositional to the audience. 

From the address bar of your web browser copy the url of the 
website, where the concert resides and then execute the following command:

    $ python3 WDR3_concert_downloader/ <url> -o <file.mp3>

where e.g.
url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html

Note: if multiple mp3 media objects are available on the website provided,
files will be downloaded and named according the scheme
file.mp3, file(1).mp3, file(2).mp3, etc. in the order the objects are 
encountered in the html soup scan.

Runs with Python3.10

On a Linux OS [download](https://github.com/Tamburasca/WDR3_concert_downloader/releases)
the executable file as was bundled with PyInstaller and run (sorry, no Windows 10/11 
version available yet):

    $ ./WDR3_concert_downloader <url> -o <file.mp3>

Note: this downloader is not supported by the WDR broadcasting organization, 
thus is inofficial! The current application supplements 
[Streamripper](https://streamripper.sourceforge.net/) 
that creates a native audio file from a broadcaster's mp3 livestream.

I found no way to downgrade the bitrate of the mp3 file to a smaller 
size without having to install **ffmpeg** or an add-on for **sox** locally. 
Suggestions welcome!