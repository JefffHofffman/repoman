#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def co_deco(func):
    def wrapper(*a, **kw):
        cr = func(*a, **kw)
        next(cr)
        return cr
    return wrapper

MAX_BUF = 2**14
class BufferOverflow(Exception):
    pass

@co_deco
def deframe(maxbuf=MAX_BUF):
    buf = bytearray()
    pos = 0
    delim = b'\n'
    
    def read_until(sep, end=None):
        nonlocal pos, buf
        i = buf.index(sep, pos, end)
        ret = buf[:i] #drop delim
        del buf[:i+len(delim)]
        pos = 0
        return ret

    def gen_all():
        try:
            while True:
                yield read_until(delim)
        except ValueError:
            pass
    
    while True:
        moar = yield gen_all()
        if len(moar) + len(buf) > maxbuf:
            raise BufferOverflow(buf)
        buf += moar

import unittest
class DeframeTest(unittest.TestCase):
    def setUp(self):
        self.gen = deframe()
        
    def assert_all(self, chunk, *a):
        expects=list(a)
        g = self.gen.send(chunk)
        for actual in g:
            self.assertEqual(actual, expects.pop(0))
        self.assertFalse(expects)

    def test_noop(self):
        self.assert_all(b'')
        
    def test_empty(self):
        self.assert_all(b'\n', b'' )
        
    def test_exact_1(self):
        self.assert_all(b'hiya\n', b'hiya' )
        
    def test_exact_N(self):
        self.assert_all(b'hello\nworld\n!\n',
                        b'hello', b'world', b'!')
        
    def test_partial_1(self):
        self.assert_all(b'hi')
        self.assert_all(b'ya\n', b'hiya' )
        
    def test_partial_N(self):
        self.assert_all(b'hello\nwor', b'hello')
        self.assert_all(b'ld\n!\n', b'world', b'!')
        
    def test_max_1(self):
        m = deframe(4)
        with self.assertRaises(BufferOverflow):
            m.send(b'x'*5)
        
    def test_max_N(self):
        m = deframe(9)
        m.send(b'x'*5)
        with self.assertRaises(BufferOverflow):
            m.send(b'x'*5)
            
    def test_max_ok(self):
        m = deframe(9)
        m.send(b'\n'*5)
        self.assert_all(b'hello\n', b'hello')



        
if __name__ == '__main__':
    unittest.main()