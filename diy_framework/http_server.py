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
        self._conn_timeout = None
        self.request = Request()


    async def handle_request(self):
        try:
            while not self.request.finished and not self._reader.at_eof():
                data = await self._reader.read(1024)
                if data:
                    self._reset_conn_timeout()
                    await self.process_data(data)
            if self.request.finished:
                await self.reply()
            elif self._reader.at_eof():
                raise BadRequestException()
        except (NotFoundException,
                BadRequestException) as e:
            self.error_reply(e.code, body=Response.reason_phrases[e.code])
        except Exception as e:
            logging.error(e)
            logging.error(e.__traceback__)
            self.error_reply(500, body=Response.reason_phrases[500])

        self.close_connection()


    async def process_data(self, data):
        self._buffer.extend(data)

        self._buffer = self.http_parser.parse_into(
            self.request, self._buffer)

    def close_connection(self):
        logging.debug('Closing connection')
        self._cancel_conn_timeout()
        self._writer.close()

    def error_reply(self, code, body=''):
        response = Response(code=code, body=body)
        self._writer.write(response.to_bytes())
        self._writer.drain()

    async def reply(self):
        logging.debug('Replying to request')
        request = self.request
        handler = self.router.get_handler(request.path)

        response = await handler.handle(request)

        if not isinstance(response, Response):
            response = Response(code=200, body=response)

        self._writer.write(response.to_bytes())
        await self._writer.drain()

    def _conn_timeout_close(self):
        self.error_reply(500, 'timeout')
        self.close_connection()

    def _reset_conn_timeout(self, timeout=TIMEOUT):
        self._cancel_conn_timeout()
        self._conn_timeout = self.loop.call_later(
            timeout, self._conn_timeout_close)

    def _cancel_conn_timeout(self):
        if self._conn_timeout:
            self._conn_timeout.cancel()
