import asyncio

from http_utils import Request, Response


TIMEOUT = 5
RESPONSE_TIMEOUT = 10


class HTTPConnection(asyncio.Protocol):
    def __init__(self, router, http_parser):
        self.http_parser = http_parser
        self.router = router
        self._buffer = bytearray()
        self._c_timeout = self._reset_c_timeout()
        self.request = Request()

    def _reset_c_timeout(self, timeout=TIMEOUT):
        self._cancel_c_timeout()
        self._c_timeout = asyncio.get_event_loop().call_later(
            timeout, self.close_connection)

    def _cancel_c_timeout(self):
        if self._c_timeout:
            self._c_timeout.cancel()

    def close_connection(self):
        self._cancel_c_timeout()
        self.transport.close()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.close()

    def write_reply(self, data):
        self.transport.write(data)

    def error_reply(self, code, body=b''):
        response = Response(code=code, body=bytes(body))
        self.write_reply(response.to_bytes())
        self.close_connection()

    def reply(self):
        request = self.request
        self.request = None
        handler = yield from self.router.get_handler(request)
        response = handler.handle(request)

        if not isinstance(response, Response):
            response = Response(code=200, body=response)

        self.write_reply(response.to_bytes())
        self.close_connection()


    def data_received(self, data):
        self._buffer.extend(data)
        try:
            self._buffer = self.http_parser.parse_into(self.request, self._buffer)
            if self.request.finished:
                self._cancel_c_timeout()
                self.reply()
            else:
                # wait for more stuff
                self._reset_c_timeout()
        except (NotFoundException, BadRequestException) as e:
            self.error_reply(e.code, body=Response.reason_phrases[e.code])
        except Exception:
            self.error_reply(500, body=Response.reason_phrases[500])
