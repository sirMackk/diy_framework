import asyncio

# asyncio.Protocol
TIMEOUT = 5
RESPONSE_TIMEOUT = 10

class Request(object):
    def __init__(self):
        self.method = None
        self.path = None
        self.path_params = {}
        self.headers = {}
        self.body = None
        self.body_raw = None
        self.query_params = None
        self.finished = False

    def parse_head(self, request_line_and_headers):
        request_line = request_line_and_headers[0]
        # get request line
        self.method, self.path = request_line.split(b' ')[:2]

        # parse query params
        self.query_params = self.parse_query_params(self.path)

        # parse headers
        for line in request_line_and_headers[1:]:
            header, value = line.split(b' ')
            self.headers[header] = value

    def parse_query_params(self):
        pass

class Response(object):
    def __init__(self, code=200, body=b'', **kwargs):
        self.code = code
        self.body = body
        self.headers = kwargs.get('headers', {})
        self.headers['content-type'] = kwargs.get('content_type', 'text/html')

    def _build_response(self):
        # generate response line
        # generate headers - type, length
        # generate body
        pass

    def __repr__(self):
        pass


class HTTPConnection(asyncio.Protocol):
    def __init__(self, host, router):
        self.router = router
        self._buffer = bytearray()
        self._c_timeout = self._reset_c_timeout()
        self.finished = False

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

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.close()

    async def write_reply(self, data):
        self.transport.write(data)

    def reply(self):
        try:
            handler = self.router.get_handler(request)
            response = await handler.handle(request)

            if not isinstance(response, Response):
                response = Response(code=200, body=response)
        except NotFoundException:
            response = Response(code=404, body=b'Not Found')
        self.write_reply(response)
        self.close_connection()


    def data_received(self, data):
        # HTTPConnection should know about crlf, Request should.
        # This should be redone so that HTTPConnection only knows
        # about terminators n stuff.
        self._buffer.extend(data)
        if b'\x0d\x0a\x0d\x0a' in data:
            # got end of headers
            request = self._initial_parse()
            if request.finished:
                self._cancel_c_timeout()
                self.reply(request)
        else:
            # wait for more stuff
            self._reset_c_timeout()

    async def _parse_initial(self):
        # HTTPConnection should have knowledge of crlf and other request
        # specific items. All of this should be moved into Request.
        request = Request()
        # break intro from body
        request_boundry = self._buffer.index(b'\r\n\r\n')
        request_line_and_headers = self._buffer[:request_boundry].split(b'\r\n')

        request.parse_head(request_line_and_headers)
        # remove intro from buffer
        self._buffer = self._buffer[request_boundry:]

        # false if waiting for request body.
        # move into request later
        request.finished = True

        return request

    async def _parse_body(self):
        pass


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
