#!/usr/bin/env python3

import os
import random
import time
from queue import Queue
from threading import Thread, Event
from typing import Generator, Iterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import StreamingResponse, PlainTextResponse, FileResponse
from starlette.datastructures import Headers
from tinytag import TinyTag

ICY_METADATA_INTERVAL = 16 * 1024  # bytes
ICY_BYTES_BLOCK_SIZE = 16  # bytes
ZERO_BYTE = b"\0"
TIME_INJECT = 60  # metadata injects in seconds

SOURCE_PATH = os.path.dirname(os.path.abspath(__file__))
FAVICON_ICO = f"{SOURCE_PATH}/../img/favicon.png"
PATH = "/app/data/"  # where the mp3 reside inside docker
# for testing define environment variable MP3_DIR to overwrite
if p := os.getenv("MP3_DIR"): PATH = p

evts = list()  # list of threads, queues, and events for subsequent cleansing


class RingMemory(object):
    """
    Ring memory iterator for the mp3 files in the given path.
    It shuffles the files and provides an eternal iterator that will
    return the next file in the list. When the end of the list is reached,
    it will return the first file again.
    """
    def __init__(self):
        self.__files = [f for f in os.listdir(PATH)
                        if os.path.isfile(PATH + f) and f.endswith(".mp3")]
        random.shuffle(self.__files)
        self._iter = iter(self.__files)

    def __iter__(self) -> Iterator[object]:
        return self

    def __next__(self) -> str:
        try:
            return next(self._iter)
        except StopIteration:
            # reset iterator and provide first element
            self._iter = iter(self.__files)
            return next(self._iter)


eternal_iterator: RingMemory = RingMemory()


def mp3_metadata(
        filepath: str
) -> dict:
    """
    Metadata extraction from mp3 file using TinyTag.
    Returns a dictionary with metadata fields that are not None.
    :param filepath:
    :return:
    """
    tag: TinyTag = TinyTag.get(filename=filepath)
    metadata = {
        "album": tag.album,  # album as string
        "albumartist": tag.albumartist,  # album artist as string
        "artist": tag.artist,  # artist name as string
        "comment": tag.comment,  # file comment as string
        "composer": tag.composer,  # composer as string
        "disc": tag.disc,  # disc number as integer
        "disc_total": tag.disc_total,  # total number of discs as integer
        "genre": tag.genre,  # genre as string
        "title": tag.title  # title of track as string, mp3-filename otherwise
        if tag.title else os.path.basename(filepath).rstrip(".mp3"),
        "track": tag.track,  # track number as integer
        "track_total": tag.track_total,  # total number of tracks as integer
        "year": tag.year,  # year or date as string
        "bitdepth": tag.bitdepth,  # bitdepth as integer (for lossless audio)
        "bitrate": round(tag.bitrate),  # bitrate in kBits/s as float
        "duration": tag.duration,  # audio duration in seconds as float
        "samplerate": tag.samplerate  # samples per second as integer
    }

    return {
        k: v for k, v in metadata.items() if v is not None
    }


def header(
        meta: dict
) -> dict:
    """
    Server header for the streaming response. This is the header that will be
    sent to the client. If 'icy-metadata' == '1' is received from the client,
    the response header comprises headers['icy-metaint'] = ICY_METADATA_INTERVAL
    as well.
    :param meta:
    :return:
    """
    head = {
        "content-type": "audio/mpeg",
        "Pragma": "no-cache",
        "Cache-Control": "max-age=0, no-cache, no-store, must-revalidate",
        "Connection": "Close, close", # "Keep-Alive",
        "Transfer-Encoding": "chunked",
        "icy-br": str(meta.get('bitrate')),
        "icy-samplerate": str(meta.get('samplerate')),
        "icy-description": "Album: {} - Artist: {}".format(
            meta.get('album', "unknown"),
            meta.get('artist', "unknown")
        ),
        "icy-genre": "Genre: {}".format(meta.get('genre', "unknown")),
        "icy-name": meta.get('title', "unknown"),
        "icy-public": "0",
        "icy-url": "https://github.com/Tamburasca/WDR3_concert_downloader"
    }

    return {
        k: v for k, v in head.items() if v is not None
    }


def injector(
        q: Queue,
        event: Event,
        msg: str
) -> None:
    """
    Injector thread that puts a message into the queue every TIME_INJECT seconds.
    This is used to inject metadata into the stream, i.e. StreamTitle
    The thread will stop when the event is set. The queue will be cleaned up
    at the end of the thread.
    :param q:
    :param event:
    :param msg:
    :return: None
    """
    i = 0  # count up for demoing
    while True:
        if event.is_set(): break
        if q.empty():
            # print("put:", msg + "_" + str(i))
            q.put(msg + "_" + str(i))
            i += 1
        time.sleep(TIME_INJECT)
    # clean up the queue, there should be only one item left
    if not q.empty():
        q.get_nowait()
        q.task_done()
    print("Stopping thread ... killing the zombie!")


def preprocess_metadata(
        metadata: str = "META_EVENT"
) -> bytes:
    """
    Preprocess metadata for ICY format.
    This function formats the metadata string into the ICY format
    and returns it as bytes.
    See also for guidance
    https://stackoverflow.com/questions/79142077/how-to-send-icy-format-message-in-audio-stream-from-server-in-python
    :param metadata: string to be published
    :return:
    """
    icy_metadata_formatted = f"StreamTitle='{metadata}';".encode()
    icy_metadata_block_length = len(icy_metadata_formatted)
    icy_no_blocks = -(-icy_metadata_block_length // ICY_BYTES_BLOCK_SIZE)
    if icy_no_blocks > 255:
        raise RuntimeError
    r = (
        # number of blocks of ICY_BYTES_BLOCK_SIZE needed for this meta message
        # (NOT including this byte), ceil notation
            icy_no_blocks.to_bytes(1, byteorder="big")
        # meta message encoded
            + icy_metadata_formatted
        # zero-padded tail to fill the last ICY_BYTES_BLOCK_SIZE
            + (icy_no_blocks * ICY_BYTES_BLOCK_SIZE - icy_metadata_block_length)
            * ZERO_BYTE
    )

    return r


def iterfile_mod(
        path: str,
        request_headers: Headers = None,
        msg: str = "",
        bitrate: float = None,
) -> Generator[bytes, None, None]:
    """
    Generator that yields chunks of the mp3 file. If the flag is set, it will
    also yield metadata. The stream is delayed by a retention time, depending on
    the bitrate and the ICY_METADATA_INTERVAL.
    :param path: path to the mp3 file
    :param request_headers: headers of the request, used to identify the client
    :param msg: msg to be injected into the stream
    :param bitrate: bitrate of the mp3 file in kBits/s
    :return: Iterator[bytes] for StreamingResponse
    :raises RuntimeError: if the number of blocks exceeds 255
    :raises ValueError: if the retention time - in case the stream is paused
    by the client - becomes negative, i.e. discontinues the byte stream
    :raises HTTPException: if the file is not found or any other error occurs
    """
    q: Queue = None

    if flag := request_headers.get('icy-metadata') == '1':
        q = Queue()
        event = Event()
        t = Thread(
            target=injector,
            args=(q, event, msg,))
        t.start()

        if evts:
            print("Items in thread list (Event: 'is set' will be deleted):")
        for item in evts:
            print(item)
        for v in filter(lambda person: person['client'] ==
                                       request_headers['user-agent'], evts):
            v['event'].set()
            if not v['thread'].is_alive():
                v['thread'].join()
                v['queue'].join()
                # delete all inactive instances
                del v['event']
                del v['queue']
                del v['thread']
                evts.remove(v)  # remove old items from list
        evts.append(
            {
                'client': request_headers['user-agent'],
                'thread': t,
                'queue': q,
                'event': event
            })

    retention = ICY_METADATA_INTERVAL / (bitrate * 1000 / 8)
    correction = 0.
    t_total = 0.

    with open(
            file=path,
            mode="rb") as mp3_stream:
        t_start = time.time()

        while chunk := mp3_stream.read(ICY_METADATA_INTERVAL):
            yield chunk

            if flag:
                if q.empty():
                    yield ZERO_BYTE
                else:  # get a special signal we can send some metadata
                    msg = q.get_nowait()
                    q.task_done()
                    yield preprocess_metadata(metadata=msg)
                try:
                    time.sleep(retention - correction)
                # if streaming is discontinued, sleep value may become negative
                # for the very last yield
                except ValueError:
                    break
                t_total += retention
                correction = time.time() - t_start - t_total
                # print(time.time() - t_start, t_total)
    print("End of method reached, last message: ", msg)


app: FastAPI = FastAPI(
    docs_url=None,
    redoc_url=None,
    title="Internetradio Web Server"
)


@app.get(
    path="/api/webradio",
    tags=[""],
    name="Streaming A Collection Of MP3-Files Randomly")
async def post_media_stream(request: Request):
    request_headers = request.headers
    print("/api/webradio caller: ", request_headers)

    try:
        while True:
            item = next(eternal_iterator)
            meta = mp3_metadata(filepath=PATH + item)
            print("metadata: {}".format(meta))
            msg = "Title: {} - Album: {} - Artist: {}".format(
                meta.get('title', "unknown"),
                meta.get('album', "unknown"),
                meta.get('artist', "unknown")
            )
            print("{0} Currently playing: {1}"
                  .format(time.asctime(time.localtime()),
                          item))
            headers: dict = header(meta=meta)
            if request_headers.get('icy-metadata') == '1':
                # enhance headers by ICY_METADATA_INTERVAL
                headers['icy-metaint'] = str(ICY_METADATA_INTERVAL)

            return StreamingResponse(
                content=iterfile_mod(
                    path=PATH + item,
                    request_headers=request.headers,
                    msg=msg,
                    bitrate=meta.get('bitrate')),
                media_type="audio/mpeg",
                headers=headers)

    except StopIteration:
        raise HTTPException(
            status_code=404,
            detail="No streamable item available.")

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e))


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(FAVICON_ICO)


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(openapi_url=app.openapi_url,
                               title="Ralf's Webradio",
                               swagger_favicon_url="/favicon.ico")


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url=app.openapi_url,
                          title="Ralf's Webradio",
                          redoc_favicon_url="/favicon.ico")


@app.get(path="/", include_in_schema=False)
def nogo():
    return PlainTextResponse(
        "No trespassing on this Internetradio Web Server\n"
        "We'll be watching you. Don't you ever dare, never ever!")


def main() -> None:
    import uvicorn

    config = {
        "host": "0.0.0.0",
        "port": 5011,  # Testing environment
        "log_level": "debug"
    }

    # kick off Asynchronous Server Gateway Interface (ASGI) webserver
    uvicorn.run(app=app,
                **config,
                )
