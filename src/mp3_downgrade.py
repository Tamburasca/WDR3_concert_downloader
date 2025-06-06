"""
Downgrade the quality of a mp3 input file for a smaller sized output file.
A mp3 input file is read and converted to a wav file stored temporily in memory,
subsequently converted again to a mp3 file by multiplying a factor <1
to the bit-rate.

We utilized a template provided by
https://github.com/miarec/pymp3
"""

import mp3
import wave
import os
import re
from io import BytesIO
from argparse import ArgumentParser
from typing import Generator
from math import ceil


class Range(object):
    def __init__(self, scope: str):
        r = re.compile(
            r'^([\[\]]) *([-+]?(?:\d*\.\d+|\d+\.?)(?:[Ee][+-]?\d+)?) *'
            r', *([-+]?(?:\d*\.\d+|\d+\.?)(?:[Ee][+-]?\d+)?) *([\[\]])$'
        )
        try:
            i = list(re.findall(r, scope)[0])
            if float(i[1]) >= float(i[2]): raise ArithmeticError
        except (IndexError, ArithmeticError):
            raise SyntaxError("Error with the range provided!")
        self.__st = '{}{}, {}{}'.format(*i)
        i[0], i[3] = {'[': '<=', ']': '<'}[i[0]], {']': '<=', '[': '<'}[i[3]]
        self.__lambda = "lambda item: {1} {0} item {3} {2}".format(*i)
    def __eq__(self, item: float) -> bool: return eval(self.__lambda)(item)
    def __contains__(self, item: float) -> bool: return self.__eq__(item)
    def __iter__(self) -> Generator[object, None, None]: yield self
    def __str__(self) -> str: return self.__st
    def __repr__(self) -> str: return self.__str__()


def downgrade(
        *,
        factor: float,
        input_file: str,
        output_file: str
) -> int:
    memory_file = BytesIO()

    with (open(input_file, "rb") as read_file,
          wave.open(memory_file, 'wb') as wav_file):
        decoder = mp3.Decoder(read_file)

        sample_rate = decoder.get_sample_rate()
        nchannels = decoder.get_channels()
        bit_rate = decoder.get_bit_rate()
        print(
            f"Input mp3-file '{input_file}' parameter:\n"
            f"Number of channels: {nchannels}\n"
            f"Sample rate: {sample_rate} samples/second\n"
            f"Bit rate: {bit_rate} kb/second\n"
            f"Layer: {decoder.get_layer()}\n"
            f"Mode: {decoder.get_mode()}\n"
        )
        wav_file.setnchannels(nchannels)
        # Only PCM 16-bit sample size is supported for reconversion to mp3
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        while True:
             pcm_data = decoder.read(4000)
             if not pcm_data:
                 break
             else:
                 wav_file.writeframes(pcm_data)

    print("Writing to output file ...\n")
    memory_file.seek(0)

    with (open(output_file, "wb") as write_file,
          wave.open(memory_file) as wav_file):
        encoder = mp3.Encoder(write_file)

        frame_rate = wav_file.getframerate()
        nchannels = wav_file.getnchannels()
        bit_rate = ceil(bit_rate * factor)

        encoder.set_bit_rate(bit_rate)
        encoder.set_sample_rate(frame_rate)
        encoder.set_channels(nchannels)
        encoder.set_quality(2)   # 2-highest, 7-fastest
        encoder.set_mode(
            mp3.MODE_STEREO if nchannels == 2 else mp3.MODE_SINGLE_CHANNEL
        )
        while True:
            pcm_data = wav_file.readframes(8000)
            if pcm_data:
                encoder.write(pcm_data)
            else:
                encoder.flush()
                break
        print(
            f"Output mp3-file '{output_file}' parameter:\n"
            f"Number of channels: {nchannels}\n"
            f"Frame rate: {frame_rate} samples/second\n"
            f"Bit rate: {bit_rate} kb/second\n"
            f"Mode: {mp3.MODE_STEREO 
            if nchannels == 2 else mp3.MODE_SINGLE_CHANNEL}"
        )

    return 0


def main() -> None:
    parser = ArgumentParser(
        description="Downgrades audio mp3 files from WDR3 concert web sites.")
    parser.add_argument(
        '-f',
        '--factor',
        required=True,
        help='Downgrade factor',
        type=float,
        choices=Range('[0.1, 1['),
    )
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        help='Input file (.mp3)')
    parser.add_argument(
        '-o',
        '--output',
        nargs='?',
        help='Output file (.mp3) (default=<input_file>_down.mp3)')

    if parser.parse_args().output is None:
        output_file = os.path.splitext(parser.parse_args().input)[0] \
                      + "_down.mp3"
    else:
        output_file = parser.parse_args().output

    exit(
        downgrade(
            factor=parser.parse_args().factor,
            input_file=parser.parse_args().input,
            output_file=output_file
        ))


if __name__ == '__main__':
    main()