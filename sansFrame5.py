#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import exit

def co_deco(func):
    def wrapper(*a, **kw):
        cr = func(*a, **kw)
        next(cr)
        return cr
    return wrapper

MAX_BUF = 2**14
class BufferOverflow(Exception):
    pass
class FrameError(Exception):
    pass

def buf_access(maxbuf):
    ''' closure to create bytearray instance with read/write functions on it '''
    buf = bytearray()
    pos = 0
    
    def read_until(sep, end=None):
        nonlocal pos, buf
        
#        i = buf.find(sep, pos, end)
#        if i < 0:
#            if end and len(buf) > end:
#                raise FrameError
#            pos = max(0, len(buf) - len(sep))
#            return None
#        
        i = -1
        while i < 0:
            if end and len(buf) > end:
                raise FrameError
            pos = max(0, len(buf) - len(sep))
            print ('\tF ', i)
            feed((yield))
#            feed((yield from ()))
            i = buf.find(sep, pos, end)
            print ('\ti ', i)

        ret = buf[:i] #drop seperator
        del buf[: i+len(sep)]
        pos = 0
        print ('INNER\t', ret)
#        yield ret
        return ret
    
    def feed(chunk):
        nonlocal buf
        if chunk:
            if len(chunk) + len(buf) > maxbuf:
                raise BufferOverflow(buf)
            buf += chunk
#        else:
#            raise StopIteration
        
    return read_until, feed
#
##@co_deco    
#def deframe(proto, maxbuf=MAX_BUF, **proto_kw):
#    '''
#    main sync co-routine that executes a user-provided protocol
#    each send of bytes yields a generator of bytearray messages
#    '''
#    rd, wr = buf_access(maxbuf)
#    p = proto(rd, **proto_kw)
#    @co_deco    
#    def ret():
#        (yield from p)
#    return ret


import unittest
class InternalTest(unittest.TestCase):
    def test_found(self):
        
        def p2(g):
          while True:  
            x = yield from g()
            print ('\t\tx', x)
            y = yield from g()
            print ('\t\ty', y)
            yield x+b':'+y
        
        def top(proto):
            buf = bytearray()
            
            def gen():
                nonlocal buf
                while True:
                    if b'x' in buf:
                        ret = buf[:1]
                        del buf[:1]
                        return ret
                    yield
                    
            p = proto(gen)

            def snd(chunk):
                nonlocal buf
                if chunk:
                    buf += chunk
                print (f'\t\t\tbuf {buf}')
                
                for a in p:
                    print ('\ta', a)
                    if a is None:
                        return
                    yield a
            return snd
        
        s = top(p2)
        
#        for r in [b'cccx', b'dx', b'ex']:
        for r in [b'x', b'dxe', b'ff', b'gggx']:
            for i, v in enumerate(s(r)):
                if i > 4: break
                print (i, v)
            print ('looped')




class DeframeTest(unittest.TestCase):
    @staticmethod
    def line_proto(read_until, delim=b'\n', **kw_ignored):
        '''
        example protocol generator
        signature is proto(rd_func, **kw) -> yield each parsed message (may be empty)
        return None when all messages consumed to terminate generator 
        '''
        while True:
            msg = (yield read_until(delim))
            print (msg, msg.decode().upper())
            yield msg.decode().upper()
#    def setUp(self):
#        self.gen = deframe(self.line_proto)
#        
#    def assert_all(self, chunk, *a):
#        expects=list(a)
#        g = self.gen.send(chunk)
#        for actual in g:
#            self.assertEqual(actual, expects.pop(0))
#        self.assertFalse(expects)

#    def test_noop(self):
#        self.assert_all(b'')
#        
#    def test_empty(self):
#        self.assert_all(b'\n', b'' )
#        
#    def test_exact_1(self):
#        self.assert_all(b'hiya\n,', 'HIYA' )
#      
#    def test_exact_N(self):
#        self.assert_all(b'hello\nworld\n!\n',
#                        b'hello', b'world', b'!')
#        
#    def test_partial_1(self):
#        self.assert_all(b'hi')
#        self.assert_all(b'ya\n', b'hiya' )
#        
#    def test_partial_N(self):
#        self.assert_all(b'hello\nwor', b'hello')
#        self.assert_all(b'ld\n!\n', b'world', b'!')\
#
#    def test_max_1(self):
#        m = deframe(self.line_proto, maxbuf=4)
#        with self.assertRaises(BufferOverflow):
#            list(m.send(b'x'*5))
#        
#    def test_max_N(self):
#        m = deframe(self.line_proto, maxbuf=9)
#        list(m.send(b'x'*5))
#        with self.assertRaises(BufferOverflow):
#            m.send(b'x'*5)
#            
#    def test_max_ok(self):
#        m = deframe(self.line_proto, maxbuf=9)
#        list(m.send(b'\n'*5))
#        msgs = list(map(bytes, m.send(b'hello\n')))
#        self.assertEqual(msgs, [b'hello'])
#
#    def test_delim(self):
#        m = deframe(self.line_proto, delim=b'\r\n')
#        msgs = list(map(bytes, m.send(b'hello\r\nworld\n!\r\n')))
#        self.assertEqual(msgs, [b'hello', b'world\n!'])

#        
#        
#
#################################################################
## Example
#################################################################
#_RECEIVE_SIZE = 4096  # pretty arbitrary
#import trio
#from trio.testing import memory_stream_pair
#async def main():    
#    # so sender.aclose() ripples to receiver
#    wire = trio.StapledStream(*memory_stream_pair())
#    
#    async def sender():
#        await wire.send_all(b"one\r\n\r\n")
#        await wire.send_all(b"two\r\n\r\n")
#        await wire.send_all(b"split-up ")
#        await wire.send_all(b"message\r\n\r")
#        await wire.send_all(b"\n")
#        await wire.aclose()
#        
#    def line_proto(read_until, delim=b'\n', **kw_ignored):
#        while True:
#            msg = read_until(delim)
#            if msg is None:
#                return
#            yield msg
#                        
#    async def pump(reader, sync_coro):
#        while True:
#            # yields sync generator of parsed messages
#            yield sync_coro.send(await reader.receive_some(_RECEIVE_SIZE))
#    try:        
#        async with trio.open_nursery() as nursery:
#            nursery.start_soon(sender)
#            sync_coro = deframe(line_proto, delim=b'\r\n\r\n')
#            async for msgs in pump(wire, sync_coro):
#                for msg in msgs:
#                    print(f"Got message: {msg}")
#                    
#    except trio.ClosedResourceError:
#        print ("done")
#        
if __name__ == '__main__':
    unittest.main()
#    trio.run(main)