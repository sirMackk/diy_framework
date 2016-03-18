import asyncio

# asyncio.Protocol
TIMEOUT = 10

class Request(object):
    def __init__(self):
        self.method = None
        self.path = None
        self.headers = {}
        self.body = None
        self.body_raw = None
        self.query_params = None

    @property
    def query_params(self):
        if not self.query_params:
            # should a property mutate an object?
            self.query_params = self.parse_query_params(self.path)
        return self.query_params

class HTTPConnection(asyncio.Protocol):
    def __init__(self, host, router):
        self.router = router
        self._buffer = bytearray()
        self._c_timeout = self._reset_c_timeout()
        self.finished = False
        self.request = Request()

    def _reset_c_timeout(self):
        if self._c_timeout:
            self._c_timeout.cancel()
        self._c_timeout = asyncio.get_event_loop().call_later(TIMEOUT, self.close_connection)

    def close_connection(self):
        if self._c_timeout:
            self._c_timeout.cancel()
        self.transport.close()

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.close()

    def start_reply(self):
        # use Router to find correct handler and pass it to the handler
        # along with a callback to self.write_reply.
        # stop c_timeout, extend it to like 30 secs

        # result = await async call handler assigned to route, pass in request values
        # OR HAVE WRITE PROTO to WRITE chunks of REPLY instead of wait for all of it
        # transport.write.result
    def data_received(self, data):
        # only handle get requests for now
        # need to use request:content-length header to
        # somehow read the request body
        # dont close connection:
        ## parse message, and call reply callback!
        self._buffer.extend(data)
        if b'\x0d\x0a\x0d\x0a' in data:
            # got end of headers
            self.finished = await self._initial_parse()
            if self.finished:
                pass
                # start reply callback
                # self.close_connection()
            else:
                self._reset_c_timeout()
        else:
            # still got stuff
            self._reset_c_timeout()

    async def _parse_initial(self):
        # break intro from body
        request_boundry = self._buffer.index(b'\r\n\r\n')
        request_line_and_headers = self._buffer[:request_boundry].split(b'\r\n')
        # remove intro from buffer
        self._buffer = self._buffer[45:]
        request_line = request_line_and_headers[0]
        # get request line
        self.request.method, self.request.path = request_line.split(b' ')[:2]

        # get headers
        for line in request_line_and_headers[1:]:
            header, value = line.split(b' ')
            self.request.headers[header] = value

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
