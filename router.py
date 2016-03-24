import re

from exceptions import NotFoundException, DuplicateRoute


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
        return re.compile(re_str)

    @classmethod
    def match_path(cls, route, path):
        match = route.match(path)
        try:
            return match.groupdict()
        except AttributeError:
            return
