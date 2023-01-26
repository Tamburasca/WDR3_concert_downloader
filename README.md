# WDR3 Concert Downloader

Downloads mp3 files from the WDR3 concert player site if
there's only an afterhearing option of 30 days and, hence, no download button
available. Copy the url of the site, where the concert resides and run the code:

    $ python3 WDR3_concert_downloader/src <url> -o <file.mp3>
where e.g.
url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html

Note: if there are multiple mp3 media objects available on the website provided,
the files will be downloaded in the following order:
file.mp3, file(1).mp3, file(2).mp3, etc. according to the objects encountered in
the html soup scan.

Contact: Dr. Ralf Antonius Timmermann, rtimmermann@astro.uni-bonn.de