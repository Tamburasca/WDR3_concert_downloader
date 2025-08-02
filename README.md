# WDR3 Concert Downloader

Downloads any audio mp3 file encountered on a WDR3 concert player website, 
if the concert is available in the media library for a re-listening over a
30-day period after its broadcast. This feature might be very useful, since 
no mp3 file download button is dispositional to the audience.  

From the address bar of your web browser copy the url of the 
website, where the concert resides and execute the following command:

    $ python3 WDR3_concert_downloader/ [-h] [-o <file>.mp3] <url>

where e.g.
url = https://www1.wdr.de/radio/wdr3/programm/sendungen/wdr3-konzert/konzertplayer-klassik-tage-alter-musik-in-herne-concerto-romano-alessandro-quarta-100.html

Note: if multiple mp3 media objects are available on the website provided,
all files will be downloaded in the order the objects are 
encountered in the html soup scan. The naming of the downloaded files follows 
the scheme file.mp3 and file_n.mp3, n being the consecutive number, starting 
at 1.

Note: this downloader is not supported by the WDR broadcasting organization, 
thus is inofficial! The current application supplements 
[Streamripper](https://streamripper.sourceforge.net/) 
that creates a native audio file from a broadcaster's mp3 livestream.

I found no way to downgrade the bitrate of the mp3 file to a smaller 
size without having to install **ffmpeg** or an add-on for **sox** locally. 
Hence, we created a mp3 downsize 
[script](https://github.com/Tamburasca/WDR3_concert_downloader/blob/master/src/mp3_downgrade.py)

    $ python3 mp3_downgrader/ -f <factor> -i <file>.mp3 [-h] [-o <file>.mp3]

where a factor is to be supplied in the range [0.1, 1.0[ 
that is multiplied with the bitrate of the 
input file. Thus, the audio quality is downgraded. 
The output file name is optional.

Furthermore, in a first draft, we provide an Internet Radio on a web server 
that is based on FastAPI utilizing its Streaming Response.
Running in a Docker container it streams a collection of mp3-files.
The files need to be made available in a 
directory specified in *.env*. and are selected randomly, when the 
method is invoked by the client. 
Text as "metadata" is injected between the byte stream chunks, if the client
reveals *icy-metadata* = '1' in its request header.
For the time being we inject mp3-metadata
present in the mp3-files, such as title, album and genre. 