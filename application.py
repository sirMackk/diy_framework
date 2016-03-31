import asyncio
import logging

import http_parser
from http_server import HTTPServer
from exceptions import DiyFrameworkException

logging_config = {
    'format': '%(asctime)s [%(levelname)s] %(message)s',
    'level': logging.DEBUG,
    'filename': None
}

logging.basicConfig(**logging_config)


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
        self._connection_handler = None
        self._loop = None

    def start_server(self):
        if not self._server:
            self.loop = asyncio.get_event_loop()
            self._server = HTTPServer(self.router, self.http_parser, self.loop)
            self._connection_handler = asyncio.start_server(
                self._server.handle_connection,
                host=self.host,
                port=self.port,
                reuse_address=True,
                reuse_port=True,
                loop=self.loop)

            logging.info("starting server")
            self.loop.run_until_complete(self._connection_handler)

            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                logging.info("Got ctrl-c sig, killing server")
            except DiyFrameworkException as e:
                logging.error("Framework failed:")
                logging.error(e.__traceback__)
            finally:
                self.loop.close()
        else:
            logging.info("Server already started - {0}".format(self))

    def __repr__(self):
        cls = self.__class__
        if self._connection_handler:
            return "{0} - Listening on: {1}:{2}".format(
                cls,
                self.host,
                self.port)
        else:
            return "{0} - Not started".format(cls)
