import logging
import asyncio

from http_utils import Request, Response
from exceptions import BadRequestException, NotFoundException, TimeoutException


TIMEOUT = 5


class HTTPServer(object):
    def __init__(self, router, http_parser, loop):
        logging.info('initing server')
        self.router = router
        self.http_parser = http_parser
        self.loop = loop
        self.connections = set()

    async def handle_connection(self, reader, writer):
        connection = HTTPConnection(self, reader, writer)
        # handle connection close here? exception, or future?
        # or await ensure_future, then remove connection?
        self.connections.add(connection)

        asyncio.ensure_future(connection.handle_request(), loop=self.loop)

    async def remove_connection(self, conn):
        self.connections.remove(conn)


class HTTPConnection(object):
    def __init__(self, http_server, reader, writer):
        self.router = http_server.router
        self.http_parser = http_server.http_parser
        self.loop = http_server.loop
        self._close_cb = http_server.remove_connection

        self._reader = reader
        self._writer = writer
        self._buffer = bytearray()
        self._c_timeout = None
        self.request = Request()

        logging.info('initing connection')

    async def handle_request(self):
        await asyncio.sleep(3)
        logging.info('initing request')
        while not self.request.finished:
            self._reset_c_timeout()
            try:
                await self.data_received(await self._reader.read(1024))
            except (NotFoundException,
                    BadRequestException,
                    TimeoutException) as e:
                self.request.finished = True
                self.error_reply(e.code, body=Response.reason_phrases[e.code])
            except Exception as e:
                logging.error(e)
                logging.error(e.__traceback__)
                self.request.finished = True
                self.error_reply(500, body=Response.reason_phrases[500])
        if not self.request.finished:
            await self.reply()
        self.close_connection()


    async def data_received(self, data):
        logging.info("data received")
        self._buffer.extend(data)

        self._buffer = self.http_parser.parse_into(
            self.request, self._buffer)

    def close_connection(self):
        logging.info("closing connection")
        self._cancel_c_timeout()
        self._close_cb(self)
        self._writer.close()

    def error_reply(self, code, body=''):
        response = Response(code=code, body=body)
        self._writer.write(response.to_bytes())
        self._writer.drain()

    async def reply(self):
        logging.info('replying')
        request = self.request
        logging.info('getting handler')
        handler = self.router.get_handler(request.path)
        logging.info('getting response')

        response = await handler.handle(request)
        logging.info('got response: {0}'.format(response))

        if not isinstance(response, Response):
            response = Response(code=200, body=response)

        self._writer.write(response.to_bytes())
        await self._writer.drain()

    def _throw_timeout(self):
        raise TimeoutException

    def _reset_c_timeout(self, timeout=TIMEOUT):
        logging.info("resetting timeout {}".format(timeout))
        self._cancel_c_timeout()
        self._c_timeout = self.loop.call_later(
            timeout, self._throw_timeout)

    def _cancel_c_timeout(self):
        logging.info('cancelling timeout')
        if self._c_timeout:
            self._c_timeout.cancel()
