# -*- coding: utf-8 -*-
import sys
import io
import trio
import logging

from trio._util import async_wraps

'''
Knowns:
    1) a log request can exert back-pressure -> await tlog.info(...)
    2) standard for lvl, filt and fmt -> logging.log() called
    3) one log msg may have many destinatons -> nursery for unit-of-work
Extras:
    4) standard dest are std handlers, convert to trio stream type?
'''

slog = logging.getLogger(__name__)
logging.critical('using parent')

# because spyder runs in the same shell, keeping handlers from previous runs?
while slog.handlers:
    slog.removeHandler(slog.handlers[0])  
if not slog.handlers:
    slog.propagate = False       
    ch = logging.StreamHandler(io.StringIO())
    formatter = logging.Formatter('{name}:{levelname}  {message}', style="{")
    ch.setFormatter(formatter)
    slog.addHandler(ch)
    slog.setLevel('DEBUG')


class TrioLogger(logging.LoggerAdapter):
    def __init__(self, dest, plain_logger, extra=None):
        super().__init__(plain_logger, extra)
        self.dest = dest    
        for name in ['log', 'debug', 'info', 'warn', 
                     'warning', 'critical', 'error']:
            meth = getattr(plain_logger, name)

            @async_wraps(self.__class__, plain_logger.__class__, name)
            async def to_dest(*a, **kw):
                meth(*a, **kw)
                hnd = plain_logger.handlers[0]
                msg = hnd.setStream(io.StringIO()).getvalue()
                if msg:
                    await dest.send_all(msg)

            setattr(self, name, to_dest)
    

class FakeConsole(trio.abc.SendStream):
    async def send_all(self, m):
#        print(F"fake:{m}", end='')
        sys.stdout.write(F"fake:{m}")
    async def wait_send_all_might_not_block(self):
        pass
    async def aclose(self):
        pass
    

async def parent():
    print("START")
    
    con = FakeConsole()
    tlog = TrioLogger(con, slog)

    async with con:
        await tlog.debug('monkey')

        await con.send_all("Message\n")
        await tlog.error("Oops")
        await tlog.error("")
        tlog.setLevel('CRITICAL')
        await tlog.warn("nvmd")
#        async with trio.open_nursery() as nursery:
#            print("parent: spawning sender...")
#            nursery.start_soon(sender, client_stream)
#
#            print("parent: spawning receiver...")
#            nursery.start_soon(receiver, client_stream)''
    print("FINISH")

trio.run(parent)