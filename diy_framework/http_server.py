import logging
import asyncio

from .http_utils import Request, Response
from .exceptions import (
    BadRequestException,
    NotFoundException,
    TimeoutException,
)


TIMEOUT = 5


class HTTPServer(object):
    def __init__(self, router, http_parser, loop):
        self.router = router
        self.http_parser = http_parser
        self.loop = loop

    async def handle_connection(self, reader, writer):
        connection = HTTPConnection(self, reader, writer)
        asyncio.ensure_future(connection.handle_request(), loop=self.loop)


class HTTPConnection(object):
    def __init__(self, http_server, reader, writer):
        self.router = http_server.router
        self.http_parser = http_server.http_parser
        self.loop = http_server.loop

        self._reader = reader
        self._writer = writer
        self._buffer = bytearray()
        self._c_timeout = None
        self.request = Request()


    async def handle_request(self):
        while not self.request.finished:
            self._reset_c_timeout()
            try:
                await self.data_received(await self._reader.read(1024))
            except (NotFoundException,
                    BadRequestException) as e:
                self.error_reply(e.code, body=Response.reason_phrases[e.code])
                break
            except Exception as e:
                logging.error(e)
                logging.error(e.__traceback__)
                self.error_reply(500, body=Response.reason_phrases[500])
                break
        if self.request.finished:
            await self.reply()
        self.close_connection()


    async def data_received(self, data):
        self._buffer.extend(data)

        self._buffer = self.http_parser.parse_into(
            self.request, self._buffer)

    def close_connection(self):
        self._cancel_c_timeout()
        self._writer.close()

    def error_reply(self, code, body=''):
        response = Response(code=code, body=body)
        self._writer.write(response.to_bytes())
        self._writer.drain()

    async def reply(self):
        request = self.request
        handler = self.router.get_handler(request.path)

        response = await handler.handle(request)

        if not isinstance(response, Response):
            response = Response(code=200, body=response)

        self._writer.write(response.to_bytes())
        await self._writer.drain()

    def _throw_timeout(self):
        raise TimeoutException

    def _reset_c_timeout(self, timeout=TIMEOUT):
        self._cancel_c_timeout()
        self._c_timeout = self.loop.call_later(
            timeout, self._throw_timeout)

    def _cancel_c_timeout(self):
        if self._c_timeout:
            self._c_timeout.cancel()
