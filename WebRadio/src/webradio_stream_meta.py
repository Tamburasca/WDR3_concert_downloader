#!/usr/bin/env python3

# see also for guidance
# https://stackoverflow.com/questions/79142077/how-to-send-icy-format-message-in-audio-stream-from-server-in-python

import os
import random
import time
from queue import Queue
from threading import Thread, Event
from typing import Generator, Iterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import StreamingResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from tinytag import TinyTag

ICY_METADATA_INTERVAL = 16 * 1024  # bytes
ICY_BYTES_BLOCK_SIZE = 16  # bytes
ZERO_BYTE = b"\0"
TIME_INJECT = 60  # metadata injects in seconds

evts = list()  # list of threads, queues, and events

PATH = "/app/data/"  # where the mp3 reside
# for testing define environment variable MP3_DIR
if p := os.getenv("MP3_DIR"): PATH = p


class RingMemory(object):
    def __init__(self):
        files = [f for f in os.listdir(PATH)
                 if os.path.isfile(PATH + f) and f.endswith(".mp3")]
        random.shuffle(files)
        self._files = files
        self._iter = iter(self._files)

    def __iter__(self) -> Iterator[object]:
        return self

    def __next__(self) -> str:
        try:
            return next(self._iter)
        except StopIteration:
            # reset iterator and provide first element
            self._iter = iter(self._files)
            return next(self._iter)


eternal_iterator: RingMemory = RingMemory()


def mp3_metadata(
        filepath: str
) -> dict:
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
        "bitrate": tag.bitrate,  # bitrate in kBits/s as float
        "duration": tag.duration,  # audio duration in seconds as float
        "samplerate": tag.samplerate  # samples per second as integer
    }

    return {
        k: v for k, v in metadata.items() if v is not None
    }


def header(
        meta: dict
) -> dict:
    head = {
        'content-type': 'audio/mpeg',
        'Pragma': 'no-cache',
        'Cache-Control': 'max-age=0, no-cache, no-store, must-revalidate',
        'Connection': 'Close, close',
        'icy-br': str(meta.get('bitrate')),
        'icy-samplerate': str(meta.get('samplerate')),
        'icy-description': 'album: {} - artist: {}'.format(
            meta.get('album', 'unknown'),
            meta.get('artist', 'unknown')
        ),
        'icy-genre': meta.get('genre', 'unknown'),
        'icy-name': meta.get('title', 'unknown'),
        'icy-public': '0',
        'icy-url': 'https://github.com/Tamburasca/WDR3_concert_downloader'
    }

    return {
        k: v for k, v in head.items() if v is not None
    }


def injector(
        q: Queue,
        event: Event,
        msg: str
) -> None:
    i = 0  # count up for demoing
    while True:
        if event.is_set(): break
        if q.empty():
            # print("put:", msg + "_" + str(i))
            q.put(msg + "_" + str(i))
            i += 1
        time.sleep(TIME_INJECT)
    # clean up the queue
    if not q.empty():  # there should be only one item in the queue
        q.get_nowait()
        q.task_done()
    print("Stopping previous thread ... killing the zombie!")


def preprocess_metadata(
        metadata: str = "META_EVENT"
) -> bytes:
    icy_metadata_formatted = f"StreamTitle='{metadata}';".encode()
    icy_metadata_block_length = len(icy_metadata_formatted)
    if -(icy_metadata_block_length // -ICY_BYTES_BLOCK_SIZE) > 255:
        raise RuntimeError
    r = (
        # number of blocks of ICY_BYTES_BLOCK_SIZE needed for this meta message
        # (NOT including this byte), ceil notation
            (-(icy_metadata_block_length //
               -ICY_BYTES_BLOCK_SIZE)).to_bytes(1, byteorder="big")
            # meta message encoded
            + icy_metadata_formatted
            # zero-padded tail to fill the last ICY_BYTES_BLOCK_SIZE
            + ((ICY_BYTES_BLOCK_SIZE -
                icy_metadata_block_length % ICY_BYTES_BLOCK_SIZE)
               % ICY_BYTES_BLOCK_SIZE * ZERO_BYTE)
    )
    # print(r)  # for testing
    return r


def iterfile_mod(
        path: str,
        request_headers: Request.headers = None,
        msg: str = "",
        bitrate: float = None,
        flag: bool = False,
) -> Generator[bytes, None, None]:
    q: Queue = None

    if flag:
        q = Queue()
        event = Event()
        t = Thread(
            target=injector,
            # daemon=True,  # we will join anyway
            args=(q, event, msg,))
        t.start()

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
                time.sleep(retention - correction)
                t_total += retention
                # next one to consider
                correction = time.time() - t_start - t_total
                # print(time.time() - t_start, tot)
    print("End of method reached, last message: ", msg)


app: FastAPI = FastAPI(
    docs_url=None,
    redoc_url=None,
    title="Internetradio Web Server"
)
app.mount(
    path="/img",
    app=StaticFiles(directory="img"),
    name="img"
)


@app.get(
    path="/api/webradio",
    tags=[""],
    name="Streaming A Collection Of MP3-Files Randomly")
async def post_media_stream(request: Request):
    request_headers = request.headers
    print("/api/webradio caller: ", request_headers)
    flag_icy_metadata = False
    if request_headers.get('icy-metadata', '0') == '1':
        flag_icy_metadata = True

    try:
        while True:
            item = next(eternal_iterator)
            meta = mp3_metadata(filepath=PATH + item)
            print("metadata: {}".format(meta))
            msg = "{} - {} - {}".format(
                meta.get('title', "unknown"),
                meta.get('album', "unknown"),
                meta.get('artist', "unknown")
            )
            print("{0} Currently playing: {1}"
                  .format(time.asctime(time.localtime()),
                          item))
            headers: dict = header(meta=meta)
            if flag_icy_metadata:
                # enhance headers by ICY_METADATA_INTERVAL
                headers['icy-metaint'] = str(ICY_METADATA_INTERVAL)

            return StreamingResponse(
                content=iterfile_mod(
                    path=PATH + item,
                    request_headers=request.headers,
                    msg=msg,
                    bitrate=meta.get('bitrate'),
                    flag=flag_icy_metadata,
                ),
                media_type="audio/mpeg",
                headers=headers
            )

    except StopIteration:
        raise HTTPException(
            status_code=404,
            detail="No streamable item available.")

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e))


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    return get_swagger_ui_html(openapi_url=app.openapi_url,
                               title="Ralf's Webradio",
                               swagger_favicon_url="/img/favicon.png")


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url=app.openapi_url,
                          title="Ralf's Webradio",
                          redoc_favicon_url="/img/favicon.png")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("img/favicon.png")


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
        # "log_level": "debug"
    }

    # kick off Asynchronous Server Gateway Interface (ASGI) webserver
    uvicorn.run(app=app,
                **config,
                )
