import asyncio


import http_parser
from http_connection import HTTPConnection
from exceptions import DiyFrameworkException


class Application(object):
    def __init__(self,
                 router,
                 host='127.0.0.1',
                 port=8080,
                 http_parser=http_parser):
        # create ip address class
        self.router = router
        self.http_parser = http_parser
        self.host = host
        self.port = port
        self._server = None
        self._transport = None
        self._loop = None

    def start_server(self):
        if not self._server:
            self.loop = asyncio.get_event_loop()
            self.server = self.loop.create_server(
                lambda: HTTPConnection(self.router, self.http_parser),
                host=self.host,
                port=self.port,
                reuse_address=True,
                reuse_port=True)
            self.transport, _ = self.loop.run_until_complete(self.server)

            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                print("Got ctrl-c sig, killing server")
            except DiyFrameworkException as e:
                print("Framework failed:")
                print(e.__traceback__)
            finally:
                self.loop.close()
                self.transport.close()
        else:
            print("Server already started - {0}".format(self))

    def __repr__(self):
        cls = self.__class__
        if self._server:
            return "{0} - Listening on: {1}:{2}".format(
                cls,
                self.host,
                self.port)
        else:
            return "{0} - Not started".format(cls)
