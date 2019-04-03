#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import trio

PORT = 12345
BUFSIZE = 16384

#from trio.socket import getaddrinfo, SOCK_STREAM, socket

class FrameStream(trio.StapledStream):
    ''' given a Stream of X, return a Stream of Y (e.g bytes => string per line)'''
    def __init__(self, lower):
        ''' lower is SocketStream '''
        trio.StapledStream.__init__(self, lower, lower) 

    def birth(self, nursery):
        nursery.start_soon(self.sender)
        nursery.start_soon(self.receiver)
        
    async def sender(self):
        print("sender: started!")
        while True:
            data = b"hiya"
            print("sender: sending {!r}".format(data))
            await self.send_all(data)
            await trio.sleep(1)
    
    async def receiver(self):
        print("receiver: started!")
        while True:
            data = await self.receive_some(BUFSIZE)
            print("receiver: got data {!r}".format(data))
            if not data:
                print("receiver: connection closed")
                raise Exception('DONE')
        
        

async def parent():
    print("parent: connecting to 127.0.0.1:{}".format(PORT))
    client_stream = await trio.open_tcp_stream("127.0.0.1", PORT)
    async with FrameStream(client_stream) as p:
        async with trio.open_nursery() as nursery:
            print("parent: spawning ...")
            p.birth(nursery)
        
        
#
#
#async def sender(client_stream):
#    print("sender: started!")
#    while True:
#        data = b"async can sometimes be confusing, but I believe in you!"
#        print("sender: sending {!r}".format(data))
#        await client_stream.send_all(data)
#        await trio.sleep(1)
#
#async def receiver(client_stream):
#    print("receiver: started!")
#    while True:
#        data = await client_stream.receive_some(BUFSIZE)
#        print("receiver: got data {!r}".format(data))
#        if not data:
#            print("receiver: connection closed")
#            raise Exception('DONE')
#
#async def parent():
#    print("parent: connecting to 127.0.0.1:{}".format(PORT))
#    client_stream = await trio.open_tcp_stream("127.0.0.1", PORT)
#    async with client_stream:
#        async with trio.open_nursery() as nursery:
#            print("parent: spawning sender...")
#            nursery.start_soon(sender, client_stream)
#
#            print("parent: spawning receiver...")
#            nursery.start_soon(receiver, client_stream)

        
#
#
#class Proto(Stream):
#    def __init__(self, base):
#        self.base = base
#        
#    async def send_all(self, *a, **kw):
#
#        
#    def birth(self, nursery):
#        nursery.start_soon(self.sender)
#        nursery.start_soon(self.receiver)
#        
#    async def sender(self):
#        print("sender: started!")
#        while True:
#            data = b"hiya"
#            print("sender: sending {!r}".format(data))
#            await self.base.send_all(data)
#            await trio.sleep(1)
#    
#    async def receiver(self):
#        print("receiver: started!")
#        while True:
#            data = await self.base.receive_some(BUFSIZE)
#            print("receiver: got data {!r}".format(data))
#            if not data:
#                print("receiver: connection closed")
#                raise Exception('DONE')
#

trio.run(parent)
