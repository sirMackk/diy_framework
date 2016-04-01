import asyncio
import logging
import re

from .exceptions import (
    DiyFrameworkException,
    NotFoundException,
    DuplicateRoute,
)

from . import http_parser
from .http_server import HTTPServer

class App(object):
    def __init__(self,
                 router,
                 host='127.0.0.1',
                 port=8080,
                 log_level=logging.INFO,
                 http_parser=http_parser):
        # create ip address class
        self.router = router
        self.http_parser = http_parser
        self.host = host
        self.port = port
        self._server = None
        self._connection_handler = None
        self._loop = None

        self.initialize_logging(level=log_level)


    def initialize_logging(self, **log_config):
        basic_logging_config = {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
            'level': logging.DEBUG,
            'filename': None
        }

        config = {**basic_logging_config, **log_config}
        logging.basicConfig(**config)

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

            logging.info("Starting server on {0}:{1}".format(
                self.host, self.port))
            self.loop.run_until_complete(self._connection_handler)

            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                logging.info("Got signal, killing server")
            except DiyFrameworkException as e:
                logging.error("Critical framework failure:")
                logging.error(e.__traceback__)
            finally:
                self.loop.close()
        else:
            logging.info("Server already started - {0}".format(self))

    def __repr__(self):
        cls = self.__class__
        if self._connection_handler:
            return "{0} - Listening on: {1}:{2}".format(
                cls, self.host, self.port)
        else:
            return "{0} - Not started".format(cls)


class HandlerWrapper(object):
    def __init__(self, handler, path_params):
        self.handler = handler
        self.path_params = path_params
        self.request = None

    async def handle(self, request):
        return await self.handler(request, **self.path_params)


class Router(object):
    def __init__(self):
        self.routes = {}

    def add_routes(self, routes):
        for route, fn in routes.items():
            self.add_route(route, fn)

    def add_route(self, path, handler):
        compiled_route = self.__class__.build_regexp(path)
        if compiled_route not in self.routes:
            self.routes[compiled_route] = handler
        else:
            raise DuplicateRoute

    def get_handler(self, path):
        logging.debug('Getting handler for: {0}'.format(path))
        for route, handler in self.routes.items():
            path_params = self.__class__.match_path(route, path)
            if path_params is not None:
                wrapped_handler = HandlerWrapper(handler, path_params)
                return wrapped_handler

        raise NotFoundException()

    @classmethod
    def build_regexp(cls, regexp_str):
        def named_groups(matchobj):
            return '(?P<{0}>[a-zA-Z0-9_-]+)'.format(matchobj.group(1))

        re_str = re.sub(r'{([a-zA-Z0-9_-]+)}', named_groups, regexp_str)
        return re.compile('^' + re_str + '$')

    @classmethod
    def match_path(cls, route, path):
        match = route.match(path)
        try:
            return match.groupdict()
        except AttributeError:
            return
