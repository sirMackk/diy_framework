import asyncio
import unittest as t
from unittest.mock import patch, MagicMock, Mock, ANY
from collections import namedtuple


from diy_framework import http_parser
from diy_framework.http_server import HTTPConnection
from diy_framework.exceptions import TimeoutException
from diy_framework import Router


HTTPServerMock = namedtuple('HTTPServerMock', 'router, http_parser, loop')

class AsyncMock(Mock):
    def __call__(self, *args, **kwargs):
        sup = super(AsyncMock, self)
        async def coro():
            return sup.__call__(*args, **kwargs)
        return coro()

    def __await__(self):
        return self().__await__()


class TestHTTPConnection(t.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServerMock(router=None,
                                     http_parser=http_parser,
                                     loop=None)

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

        self.router = Router()
        self.server = self.server._replace(router=self.router, loop=self.loop)

        self.reader = asyncio.streams.StreamReader(loop=self.loop)
        self.writer = MagicMock(spec=asyncio.streams.StreamWriter)
        self.writer.write = MagicMock()
        self.writer.drain = AsyncMock()
        self.writer.close = MagicMock()

        self.conn = HTTPConnection(self.server, self.reader, self.writer)

    def tearDown(self):
        self.loop.stop()
        self.loop.close()

    def test_empty_get_request(self):
        mock_get_handler = AsyncMock(return_value='response')
        self.reader.feed_data(b'GET / http/1.1\r\n\r\n')

        self.router.add_route(r'/', mock_get_handler)

        self.loop.run_until_complete(self.conn.handle_request())
        self.assertTrue(self.writer.write.call_args[0][0].endswith(b'response'))

    def test_url_params_get_request(self):
        mock_get_handler = AsyncMock(return_value='response')
        self.reader.feed_data(b'GET /12/edit/bob http/1.1\r\n\r\n')

        self.router.add_route(r'/{id}/edit/{name}', mock_get_handler)

        self.loop.run_until_complete(self.conn.handle_request())
        mock_get_handler.assert_any_call(ANY, id='12', name='bob')

    def test_post_request(self):
        async def echo_coro(r):
            return bytes(r.body_raw).decode('utf-8')
        self.reader.feed_data(
            (b'POST / http/1.1\r\nContent-Length:8\r\n'
             b'Content-Type: application/x-www-form-urlencoded\r\n\r\n'
             b'abcd=123'))

        self.router.add_route(r'/', echo_coro)
        self.loop.run_until_complete(self.conn.handle_request())
        self.assertTrue(self.writer.write.call_args[0][0].endswith(b'abcd=123'))

    def test_post_large_request(self):
        async def echo_coro(r):
            return bytes(r.body_raw).decode('utf-8')
        self.reader.feed_data(
            (b'POST / http/1.1\r\nContent-Length: 2000\r\n'
             b'Content-Type: application/x-www-form-urlencoded\r\n\r\n') +
            b'abcd=12345' * 200)
        self.router.add_route(r'/', echo_coro)
        self.loop.run_until_complete(self.conn.handle_request())
        rsp_body = self.writer.write.call_args[0][0].split(b'\r\n\r\n')[1]
        self.assertEqual(len(rsp_body), 2000)


    @t.skip('')
    def test_request_timeout(self):
        self.reader.feed_data(b'GET / ')
        self.loop.run_until_complete(self.conn.handle_request())


if __name__ == '__main__':
    t.main()
