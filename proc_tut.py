#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess

import trio
from trio import Process

import contextvars

ctxv = contextvars.ContextVar('foo')

BUFSIZE = 16384

import logging
#logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)
log.error("YAWZA")

#class AsyncLogger(object):
#    ''' a SendStream impersonating a Logger '''
#    def __init__(self, stream, log):


class FileStream(trio.abc.Stream):
    def __init__(self, buf_io):
        self.wrapped = trio.wrap_file(buf_io)

    async def receive_some(self, n):
        return await self.wrapped.read(n)
    
    async def send_all(self, data):
        # note that TextIOWrapper as buf_io can alter write semantics
        return await self.wrapped.write(data) 
    
    async def wait_send_all_might_not_block(self):
        pass

    async def aclose(self):
        pass

    

class Console(trio.StapledStream):
    ''' not intedend for context mgr; entire progam is context for sys '''
    def __init__(self):
        super().__init__(FileStream(sys.stdout),
                         FileStream(sys.stdin))
        

class ProcStream(trio.StapledStream):
    def __init__(self, *a, **kw):
        std = dict(stdin=subprocess.PIPE,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE
                   )
        std.update(kw)
        self.proc = Process(*a, **std)
        super().__init__(self.proc.stdin,
                         self.proc.stdout)
    

class SshProc(Process, ):
    def __init__(self, *a):
        std = dict(stdin=subprocess.PIPE,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE
                   )
        super().__init__( *a, **std )
        
        
    async def start(self, nursery):




        
#        async def do_out(stream, tag):
#            async with stream:
#                while True:
#                    data = await stream.receive_some(BUFSIZE)
#                    print(f"{tag}: {data}")
#                    if not data:
#                        print("f{tag}: CLOSED")
#                        
#        nursery.start_soon(do_out, self.stdout, 'OUT')
#        nursery.start_soon(do_out, self.stderr, 'ERR')
        print("A")
#        await self.stdin.send_all(b"!Target1")
        await self.stdin.send_all(b"ls")
        print("B")

    
    
    
async def main():
    console = Console()
    ctxv.set('top')
    
    async def lg(msg):
        await console.send_all(F"{ctxv.get()}:::{msg}\n")
    
    await lg('\tCONSOLE\n')

    async def do_out(stream, tag):
        ctxv.set(tag)
        async with stream:
            while True:
                data = await stream.receive_some(BUFSIZE)
                await lg(data)
                print(f"{tag}: {data}")
                if not data:
                    print(f"{tag}: CLOSED")
                    
    
    
    with trio.move_on_after(2):
        async with trio.open_nursery() as nursery:
            async with ProcStream(["ssh", "localhost"]) as p:
                await p.send_all(b"ls ..\necho DELIM\n")                          
                nursery.start_soon(do_out, p.proc.stdout, 'OUT')
                nursery.start_soon(do_out, p.proc.stderr, 'ERR')
                await trio.sleep_forever()

            
                
                
                
                
#                await proc.stdin.send_all(b"ls ..\n")
#    #            await trio.sleep(3)
#                
#          
#                nursery.start_soon(do_out, proc.stdout, 'OUT')
#                nursery.start_soon(do_out, proc.stderr, 'ERR')
#                await trio.sleep_forever()
#
#            
#            await proc.start(nursery)


            
    print (p.proc.returncode)
        

            
    


trio.run(main)


