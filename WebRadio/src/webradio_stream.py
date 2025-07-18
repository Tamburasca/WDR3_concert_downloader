#!/usr/bin/env python3

# see also for guidance
# https://stackoverflow.com/questions/79142077/how-to-send-icy-format-message-in-audio-stream-from-server-in-python

import os
import random
import time
from typing import Generator, Iterator

import uvicorn
from fastapi import FastAPI, HTTPException, Request  # Header,
from fastapi.responses import StreamingResponse
from tinytag import TinyTag

ICY_METADATA_INTERVAL = 8 * 1024  # bytes
ICY_BYTES_BLOCK_SIZE = 16  # bytes
ZERO_BYTE = b"\0"

PATH = "/app/data/"
# PATH = "/home/ralf/WDR3_mp3/"  # for testing with PyCharm


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
        "year": tag.year  # year or date as string
    }
    return {
        k: v for k, v in metadata.items() if v is not None
    }


def header(
        meta: dict
) -> dict:
    return {
        "content-type": "audio/mpeg",
        "icy-description": "album: {} - artist: {}".format(  # ToDo
            meta.get('album', "unknown"),
            meta.get('artist', "unknown")
        ),
        "icy-audio-info": "test-audio-info",  # ToDo
        "icy-genre": meta.get('genre', "unknown"),
        "icy-name": meta.get('title', "unknown"),
        "icy-notice1": "notice1",  # ToDo
        "icy-notice2": "notice2",  # ToDo
        "icy-public": "1",
        # "icy-url": ""
    }


def preprocess_metadata(
        metadata: str = "META_EVENT"
) -> Generator[bytes, None, None]:
    icy_metadata_formatted = f"StreamTitle='{metadata}';".encode()
    icy_metadata_block_length = len(icy_metadata_formatted)
    return (
            # number of blocks of ICY_BYTES_BLOCK_SIZE needed for this meta message (NOT including this byte)
            (1 + (icy_metadata_block_length - 1) // ICY_BYTES_BLOCK_SIZE).to_bytes(1, byteorder="big")
            # meta message encoded
            + icy_metadata_formatted
            # zero-padded tail to fill the last ICY_BYTES_BLOCK_SIZE
            + (ICY_BYTES_BLOCK_SIZE - icy_metadata_block_length % ICY_BYTES_BLOCK_SIZE) * ZERO_BYTE
    )


# def iterfile(
#         path: str
# ) -> Generator[bytes, None, None]:
#     with open(path, mode="rb") as mp3_stream:
#         while chunk := mp3_stream.read(64 * 1024):
#             yield chunk


def iterfile_mod(
        path: str,
        msg: str = "",
        flag: bool = False
) -> Generator[bytes, None, None]:
    event = True  # ToDo: enable toggle via queue to change titles, and merge Iterfile() functions
    with open(path, mode="rb") as mp3_stream:
        while chunk := mp3_stream.read(ICY_METADATA_INTERVAL):
            yield chunk
            if flag:
                if not event:
                    yield ZERO_BYTE
                else:  # get a special signal we can send some metadata
                    event = False
                    yield preprocess_metadata(msg)  # preprocess_metadata(msg)


eternal_iterator = RingMemory()
app = FastAPI()


@app.get(path="/api/webradio")
async def post_media_file(request: Request):
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
                headers['icy-metaint'] = str(ICY_METADATA_INTERVAL)  # enhance headers by ICY_METADATA_INTERVAL

            return StreamingResponse(
                iterfile_mod(
                    path=PATH + item,
                    msg=msg,
                    flag=flag_icy_metadata
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


# this method is going to be deprecated
@app.get(path="/api/mp3")
async def post_mp3_file(request: Request):
    print("/api/mp3 caller", request.headers)

    try:
        while True:
            item = next(eternal_iterator)
            meta = mp3_metadata(filepath=PATH + item)
            print("metadata: {}".format(meta))
            print("{0} Currently playing: {1}"
                  .format(time.asctime(time.localtime()),
                          item))
            return StreamingResponse(
                iterfile_mod(
                    path=PATH + item
                ),
                media_type="audio/mpeg",
                headers=header(meta=meta)
            )

    except StopIteration:
        raise HTTPException(
            status_code=404,
            detail="No streamable item available.")

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e))


def main() -> None:
    config = {
        "host": "0.0.0.0",
        "port": 5010,
        "timeout_keep_alive": 60,
    }
    # kick off Asynchronous Server Gateway Interface (ASGI) webserver
    uvicorn.run(app=app,
                **config,
                )


if __name__ == '__main__':
    main()
