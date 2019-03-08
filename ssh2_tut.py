#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 11:36:44 2019

@author: jeffh
"""

import trio

from ssh2.session import Session

#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.connect(('localhost', 22))

#
#class FrameStream(trio.StapledStream):
#    '''
#    given a Stream of X, return a Stream of Y (e.g bytes => messages)
#    assumes encode/decode is via sync calls to_lower/from_lower
#    
#    '''
#    MAX_LOWER = 2048
#    def __init__(self, lower):
#        ''' lower is HalfClosableStream instance (e.g. SocketStream)'''
#        self.buf = b''  # TODO make type(X())
#        super().__init__(self, lower, lower)
#    
#    def to_lower(self, msg):
#        raise NotImplementedError
#    def from_lower(self):
#        ''' buf X -> one Y OR None if not enough in buf'''
#        raise NotImplementedError
#  
#    async def send_all(self, ins):
#        for i in ins:
#            data = self.to_lower(i)
#            await super().send_all(data)
#
#    async def receive_some(self, n):
#        outs = []
#        while len(outs) < n:
#            o = self.from_lower()
#            if o is None:
#                self.buf += await super().receive_some(self.MAX_LOWER)
#            else:
#                outs.append(o)
#        return outs


class SshStreamCmd(trio.StapledStream):
    ''' given tcp stream, return stream of cmdString -> (respString, errCode) '''
    def __init__(self, lower):
        super().__init__(self, lower, lower)
        self.ses =  Session()
        self.ses.handshake(lower.socket)
        self.ses.userauth_password('jeffh', '!Target1')
        self.chan = self.open_session()

    async def send_all(self, ins):
        for i in ins:
            await self.wait_send_all_might_not_block()
            self.chan.execute('echo me; exit 2')

    async def receive_some(self, n):
        outs = []
        while len(outs) < n:
            o = self.from_lower()
            if o is None:
                self.buf += await super().receive_some(self.MAX_LOWER)
            else:
                outs.append(o)
        return outs

from ssh2.error_codes import LIBSSH2_ERROR_EAGAIN

async def parent():
    tcp_stream = await trio.open_tcp_stream("127.0.0.1", 22)

    
    s = Session()
    s.handshake(tcp_stream.socket)
    s.userauth_password('jeffh', '!Target1')
    #session.agent_auth(user)
    cmd = 'echo me; exit 2'
#    channel = session.open_session()
#    channel.execute(cmd)
#    size, data = channel.read()
#    while size > 0:
#        print(data)
#        size, data = channel.read()
#    channel.close()
#    print("Exit status: %s" % channel.get_exit_status())
    s.set_blocking(False)
#    print (await tcp_stream.socket.recv(0))
    chan = s.open_session()
    print ('CHAN', chan)
    while chan == LIBSSH2_ERROR_EAGAIN:
        print("Would block on session open, waiting for socket to be ready")
        await trio.sleep(0.1)
        chan = s.open_session()
        print ('CHAN', chan)

    chan = s.open_session()
    print ('CHAN2', chan)
    while chan == LIBSSH2_ERROR_EAGAIN:
        print("Would block on session open, waiting for socket to be ready")
        await trio.sleep(0.1)
        chan = s.open_session()
        print ('CHAN2', chan)
        
    print (await tcp_stream.wait_send_all_might_not_block())
    while chan.execute(cmd) == LIBSSH2_ERROR_EAGAIN:
        print("Would block on channel execute, waiting for socket to be ready")
        await trio.sleep(0.1)
    while chan.wait_eof() == LIBSSH2_ERROR_EAGAIN:
        print("Waiting for command to finish")
        await trio.sleep(0.1)
    size, data = chan.read()
    while size == LIBSSH2_ERROR_EAGAIN:
        print("Waiting to read data from channel")
        await trio.sleep(0.1)
        size, data = chan.read()
    while size > 0:
        print(data)
        size, data = chan.read()


#
#    print("parent: connecting to 127.0.0.1:{}".format(PORT))
#    client_stream = await trio.open_tcp_stream("127.0.0.1", PORT)
#    async with NetstringStream(client_stream) as p:
#        async with trio.open_nursery() as nursery:
#            print("parent: spawning ...")
#            nursery.start_soon(line_sender, p)
#            nursery.start_soon(line_receiver, p)
            
            
        

trio.run(parent)
