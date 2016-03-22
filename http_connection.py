import asyncio
from urllib import parse

# asyncio.Protocol
TIMEOUT = 5
RESPONSE_TIMEOUT = 10

class Request(object):
    crlf = b'\x0d\x0a'
    separator = b'\x0d\x0a\x0d\x0a'

    def __init__(self):
        self.method = None
        self.path = None
        self.path_params = {}
        self.headers = {}
        self.body = None
        self.body_raw = None
        self.query_params = {}

    def parse(self, buffer):
        # add body parsing logic, based on content-length header
        if Request.separator in buffer:
            # got end of headers
            request_boundry = buffer.index(Request.separator)
            request_line_and_headers = buffer[:request_boundry].split(Request.crlf)

            self.parse_head(request_line_and_headers)
            # remove intro from buffer
            buffer = buffer[request_boundry:]

            # tmp
            if not b'content-length' in self.headers.keys():
                request.finished = True
        elif b'content-length' in self.headers.keys():
            if len(buffer) == int(self.headers[b'content-length']):
                self.parse_body(buffer)
                del buffer[:]
        return buffer

    def parse_head(self, request_line_and_headers):
        request_line = request_line_and_headers[0]
        # parse the request line
        self.method, self.path = request_line.split(b' ')[:2]

        if b'?' in self.path:
            self.parse_query_params(self.path)

        # parse headers
        for line in request_line_and_headers[1:]:
            header, value = line.split(b' ')
            self.headers[header.lower()[:-1]] = value

    def parse_body(self, buffer):
        self.raw_body = buffer
        content_type = self.headers.get(b'content-type', '')
        if content_type == 'application/x-www-form-urlencoded':
            self.body = parse.parse_qs(self.raw_body)
        elif content_type == 'application/json':
            self.body = json.dumps(self.raw_body)

    def parse_query_params(self):
        url_obj = parse.urlparse(self.path)
        self.query_params = parse.parse_qs(url_obj.query)

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
            [': '.join(k, v) for k, v in self.headers.items()])
        return b'\r\n'.join(
            [response_line.encode(), self.headers, b'\r\n', self.body])

    def to_bytes(self):
        return self._build_response().encode()


class HTTPConnection(asyncio.Protocol):
    def __init__(self, host, router):
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

    async def write_reply(self, data):
        self.transport.write(data)

    def reply(self):
        request = self.request
        self.request = None
        try:
            handler = self.router.get_handler(request)
            response = await handler.handle(request)

            if not isinstance(response, Response):
                response = Response(code=200, body=response)
        except NotFoundException:
            response = Response(code=404, body=b'Not Found')
        self.write_reply(response.to_bytes())
        self.close_connection()


    def data_received(self, data):
        self._buffer.extend(data)
        self._buffer = self.request.parse(self._buffer)
        if self.request.finished:
            self._cancel_c_timeout()
            self.reply()
        else:
            # wait for more stuff
            self._reset_c_timeout()


loop = asyncio.get_event_loop()
server = loop.create_server(proto,
                            host=host,
                            port=80,
                            reuse_address=True,
                            reuse_port=True)

transport, protocol = loop.run_until_complete(server)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

loop.close()
transport.close()
