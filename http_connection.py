import asyncio

import http_parser

# asyncio.Protocol
TIMEOUT = 5
RESPONSE_TIMEOUT = 10

class Request(object):
    def __init__(self):
        self.method = None
        self.path = None
        self.query_params = {}
        self.path_params = {}
        self.headers = {}
        self.body = None
        self.body_raw = None
        self.finished = False


class Response(object):
    reason_phrases = {
        200: 'OK',
        204: 'No Content',
        301: 'Moved Permanently',
        302: 'Found',
        304: 'Not Modified',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        451: 'Unavailable for Legal Reasons',
        500: 'Internal Server Error',
    }

    def __init__(self, code=200, body=b'', **kwargs):
        self.code = code
        self.body = body
        self.headers = kwargs.get('headers', {})
        self.headers['content-type'] = kwargs.get('content_type', 'text/html')

    def _build_response(self):
        response_line = 'HTTP/1.1 {0} {1}'.format(
            self.code, self.reason_phrases[self.code])
        self.headers = {**self.headers, **{'Content-Length': len(self.body)}}
        headers = '\r\n'.join(
            [': '.join([k, str(v)]) for k, v in self.headers.items()])
        return '\r\n'.join(
            [response_line, headers, '\r\n', self.body])

    def to_bytes(self):
        return self._build_response().encode()


class HTTPConnection(asyncio.Protocol):
    def __init__(self, http_parser, router):
        self.http_parser = http_parser
        self.router = router
        self._buffer = bytearray()
        self._c_timeout = self._reset_c_timeout()
        self.request = Request(http_parser)

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

    async def write_reply(self, data):
        self.transport.write(data)

    def reply(self):
        request = self.request
        self.request = None
        try:
            handler = self.router.get_handler(request)
            response = handler.handle(request)

            if not isinstance(response, Response):
                response = Response(code=200, body=response)
        except NotFoundException:
            response = Response(code=404, body=b'Not Found')
        self.write_reply(response.to_bytes())
        self.close_connection()


    def data_received(self, data):
        self._buffer.extend(data)
        self._buffer = self.http_parser.parse_into(self.request, self._buffer)
        if self.request.finished:
            self._cancel_c_timeout()
            self.reply()
        else:
            # wait for more stuff
            self._reset_c_timeout()


# loop = asyncio.get_event_loop()
# server = loop.create_server(lambda: HTTPConnection,
                            # host='127.0.0.1',
                            # port=80,
                            # reuse_address=True,
                            # reuse_port=True)

# transport, protocol = loop.run_until_complete(server)

# try:
    # loop.run_forever()
# except KeyboardInterrupt:
    # pass

# loop.close()
# transport.close()
