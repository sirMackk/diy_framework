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
        self.finished = False

    def parse(self, buffer):
        if Request.separator in buffer:
            # got end of headers
            request_boundry = buffer.index(Request.separator)
            request_line_and_headers = buffer[:request_boundry].split(Request.crlf)

            self.parse_head(request_line_and_headers)
            # remove intro from buffer
            buffer = buffer[request_boundry+4:].strip()

            # tmp
            if not 'content-length' in self.headers:
                self.finished = True

        if 'content-length' in self.headers:
            if len(buffer) == int(self.headers['content-length']):
                self.parse_body(buffer)
                del buffer[:]
                self.finished = True
        return buffer

    def parse_head(self, request_line_and_headers):
        request_line = request_line_and_headers[0]
        # parse the request line
        self.method, path_line = request_line.split(b' ')[:2]

        url_obj = parse.urlparse(path_line)
        self.path = url_obj.path

        if url_obj.query:
            self.parse_query_params(url_obj)

        # parse headers
        for line in request_line_and_headers[1:]:
            header, value = line.strip().split(b' ')
            header = header.decode('utf-8').lower()[:-1]
            self.headers[header] = value.decode('utf-8')

    def parse_body(self, buffer):
        self.body_raw = buffer[:]
        content_type = self.headers.get('content-type', '')
        if content_type == 'application/x-www-form-urlencoded':
            self.body = parse.parse_qs(self.body_raw)
        elif content_type == 'application/json':
            self.body = json.dumps(self.body_raw)

    def parse_query_params(self, url_obj):
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
            [': '.join([k, str(v)]) for k, v in self.headers.items()])
        return '\r\n'.join(
            [response_line, headers, '\r\n', self.body])

    def to_bytes(self):
        return self._build_response().encode()


class HTTPConnection(asyncio.Protocol):
    def __init__(self, router):
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
            response = handler.handle(request)

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
