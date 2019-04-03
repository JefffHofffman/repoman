#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import trio
from itertools import count

PORT = 12345
BUFSIZE = 16384
CONNECTION_COUNTER = count()

async def echo_server(server_stream):
    ident = next(CONNECTION_COUNTER)
    print("echo_server {}: started".format(ident))
    try:
        while True:
            data = await server_stream.receive_some(BUFSIZE)
            print("echo_server {}: received data {!r}".format(ident, data))
            if not data:
                print("echo_server {}: connection closed".format(ident))
                return
            print("echo_server {}: sending data {!r}".format(ident, data))
            await server_stream.send_all(data.upper())
    # FIXME: add discussion of MultiErrors to the tutorial, and use
    # MultiError.catch here. (Not important in this case, but important if the
    # server code uses nurseries internally.)
    except Exception as exc:
        print("echo_server {}: crashed: {!r}".format(ident, exc))

async def main():
    await trio.serve_tcp(echo_server, PORT)

trio.run(main)