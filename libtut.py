#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#from ssh2.session import Session as LibSes
#import trio
#
#
#async def main():
#    soc_strm = await trio.open_tcp_stream("127.0.0.1", 22)
#    
#    lib_ses = LibSes()
#    lib_ses.handshake(soc_strm.socket)
#    print(lib_ses.userauth_list())
#
#
#
#trio.run(main)
import asyncio, asyncssh, sys

async def run_client():
    async with asyncssh.connect('localhost', password='!Target1') as conn:
        print ('Conn', type(conn), conn)
        result = await conn.run('echo "Hello!"', check=True)
        print(result.stdout, end='')

try:
    
    
    
    
    l = asyncio.get_event_loop()
    l.create_task(run_client())
#    l.run_until_complete(run_client())
except (OSError, asyncssh.Error) as exc:
    sys.exit('SSH connection failed: ' + str(exc))