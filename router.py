import re

from exceptions import NotFoundException


class HandlerWrapper(object):
    def __init__(self, handler):
        self.handler = handler
        self.path_params = {}
        self.request = None

    def handle(self, request):
        request.path_params = {**self.path_params, **request.path_params}
        return await self.handler(request)


def named_groups(matchobj):
    return '(?P<{}>[a-zA-Z0-9_-]+)'.format(matchobj.group(1))


def build_regexp(regexp_str):
    re_str = re.sub(r'{([a-zA-Z0-9_-]+)}', named_groups, regexp_str)
    return re.compile(re_str)


class Router(object):
    def __init__(self):
        self.routes = {}

    def add_routes(self, routes):
        for route, fn in routes.items():
            self.add_route(route, fn)

    def add_route(self, path, handler):
        compiled_route = build_regexp(path)
        self.routes[compiled_route] = handler

    def get_handler(self, path):
        for route, handler in self.routes.items():
            match = route.match(path)
            if match:
                wrapped_handler = HandlerWrapper(handler)
                wrapper_handler.path_params = match.groupdict()
                return wrapped_handler

        raise NotFoundException()
