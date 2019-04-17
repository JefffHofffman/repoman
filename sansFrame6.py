#!/usr/bin/env python3
# -*- coding: utf-8 -*-

MAX_BUF = 2**14
class BufferOverflow(Exception):
    pass
class FrameError(Exception):
    pass

def deframe(proto, maxbuf=MAX_BUF, **kw_proto):
    buf = bytearray()
    pos = 0

#    def read_until(sep, start=0, stop=None):
    def read_until(sep=b'', stop=None):
        nonlocal pos, buf
        while True:
            if sep:
                i = buf.find(sep, pos, stop)
            elif stop:
                i = stop if len(buf) >= stop else -1
            else:
                raise FrameError

            if i > -1:
                ret = buf[:i] #drop seperator
                del buf[: i+len(sep)]
                pos = 0
                return ret
            if sep and stop and len(buf) > stop:
                raise FrameError
            pos = max(0, len(buf) - len(sep))
            yield
            
    p = proto(read_until, **kw_proto)

    def snd(chunk):
        nonlocal buf
        if chunk:
            if len(chunk) + len(buf) > maxbuf:
                raise BufferOverflow(buf)
            buf += chunk
        def wrapped():
            for msg in p:
                if msg is None:
                    return
                yield msg
        return wrapped()
    return snd

import unittest
class InternalTest(unittest.TestCase):
    def test_found(self):
        def simple(r, **kw_ignored):
            while True:
                yield (yield from r(b':'))
        
        gen_msgs = deframe(simple)
        self.assertEqual([], list(gen_msgs(b'4')))
        self.assertEqual([b'4'], list(gen_msgs(b':')))


class DeframeTest(unittest.TestCase):
    @staticmethod
    def line_proto(read_until, delim=b'\n', **kw_ignored):
        '''
        example protocol generator used by frame()
        signature is f(rd_func, **kw) -> yield each parsed message
        '''
        while True:
            yield (yield from read_until(delim))
            
    def setUp(self):
        self.gen = deframe(self.line_proto)
        
    def assert_all(self, chunk, *a):
        expects=list(a)
        g = self.gen(chunk)
        for actual in g:
            self.assertEqual(actual, expects.pop(0))
        self.assertFalse(expects)

    def test_noop(self):
        self.assert_all(b'')
        
    def test_empty(self):
        self.assert_all(b'\n', b'' )
        
    def test_exact_1(self):
        self.assert_all(b'hiya\n,', b'hiya' )
      
    def test_exact_N(self):
        self.assert_all(b'hello\nworld\n!\n',
                        b'hello', b'world', b'!')
        
    def test_partial_1(self):
        self.assert_all(b'hi')
        self.assert_all(b'ya\n', b'hiya' )
        
    def test_partial_N(self):
        self.assert_all(b'hello\nwor', b'hello')
        self.assert_all(b'ld\n!\n', b'world', b'!')\

    def test_max_1(self):
        m = deframe(self.line_proto, maxbuf=4)
        with self.assertRaises(BufferOverflow):
            m(b'x'*5)
        
    def test_no_drain(self):
        m = deframe(self.line_proto, maxbuf=9)
        m(b'\n'*5)
        with self.assertRaises(BufferOverflow):
            m(b'\n'*5)
            
    def test_max_ok(self):
        m = deframe(self.line_proto, maxbuf=9)
        list(m(b'\n'*5))
        msgs = list(map(bytes, m(b'hello\n')))
        self.assertEqual(msgs, [b'hello'])

    def test_delim(self):
        m = deframe(self.line_proto, delim=b'\r\n')
        msgs = list(map(bytes, m(b'hello\r\nworld\n!\r\n')))
        self.assertEqual(msgs, [b'hello', b'world\n!'])
        
    def test_end(self):
        def netstring_1k(read_until, **kw_ignored):
            while True:
                yield (yield from read_until(b':', 3))
        m = deframe(netstring_1k)
        self.assertEqual(list(m(b'42:')), [b'42'])

        with self.assertRaises(FrameError):
            list(m(b'99999:'))
            
    def test_no_sep(self):
        def any4(read_until, **kw_ignored):
            while True:
                yield (yield from read_until(stop=4))
        m = deframe(any4)
        self.assertEqual(list(m(b'12')), [])
        self.assertEqual(list(m(b'3456')), [b'1234'])


if __name__ == '__main__':
#    unittest.main( defaultTest='DeframeTest.test_max_N',)
    unittest.main()
#    trio.run(main)