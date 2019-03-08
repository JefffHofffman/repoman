#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import trio

PORT = 12345
BUFSIZE = 16384

class MyTrioError(Exception):
    pass

class FrameStream(trio.StapledStream):
    '''
    given a Stream of X, return a Stream of Y (e.g bytes => messages)
    assumes encode/decode is via sync calls
    
    '''
    def __init__(self, base):
        ''' lower is SocketStream '''
        self.base = base
        self.buf = b''
        self.state = 0
        trio.StapledStream.__init__(self, base, base)
    
    def to_base(self, msg):
        return msg + b'\n'
    
    def from_base(self):
        pos = self.buf.find(b'\n')
        ret = None
        if pos > -1:
            print ('POS', pos)
            ret = self.buf[:pos]
            self.buf = self.buf[pos+1:]
        return ret
  
    async def send_all(self, lines):
        for l in lines:
            data = self.to_base(l)
            await self.base.send_all(data)

    async def receive_some(self, n):
        ret = []
        while len(ret) < n:
            msg = self.from_base()
            if msg is None:
                self.buf += await self.base.receive_some(BUFSIZE)
            else:
                ret.append(msg)
        return ret

class NetstringStream(FrameStream):
    MAXBUF = 2**16
    def __init__(self, base):
        self.len = None
        FrameStream.__init__(self, base)
    
    def to_base(self, msg):
        return F'{len(msg)}:{msg},'.encode()
    
    def from_base(self):
        if len(self.buf) > NetstringStream.MAXBUF:
            raise MyTrioError('recieve buffer maxed out')
        ret = None
        if self.len is None:
            p = self.buf.split(b':', 1)
            if len(p) > 1:
                l, self.buf = p
                self.len = int(l)        
        elif len(self.buf) >= self.len:
            p = self.buf.split(b',', 1)
            if len(p) > 1:
                ret, self.buf = p
                self.len = None
            else:
                raise MyTrioError('Bad Netstring format')
        return ret
            


async def line_sender(client_stream):
    print("sender: started!")
    while True:
        data = ['Bravely bold Sir Robin', 'Bravely ran away']
        await client_stream.send_all(data)
        await trio.sleep(1)

async def line_receiver(client_stream):
    print("receiver: started!")
    while True:
        data = await client_stream.receive_some(1)
        print("receiver: got data {!r}".format(data))
        if not data:
            print("receiver: connection closed")
            raise Exception('DONE')

async def parent():
    print("parent: connecting to 127.0.0.1:{}".format(PORT))
    client_stream = await trio.open_tcp_stream("127.0.0.1", PORT)
    async with NetstringStream(client_stream) as p:
        async with trio.open_nursery() as nursery:
            print("parent: spawning ...")
            nursery.start_soon(line_sender, p)
            nursery.start_soon(line_receiver, p)
            
            
        

trio.run(parent)
