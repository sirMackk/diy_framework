import unittest as t

from diy_framework import Router
from diy_framework.exceptions import DuplicateRoute, NotFoundException


class TestRouter(t.TestCase):
    def setUp(self):
        self.router = Router()
        self.handler = lambda r, *args: (r, args,)

    def test_unique_route(self):
        route = r'/path'
        route2 = r'/path'

        self.router.add_route(route, self.handler)
        with self.assertRaises(DuplicateRoute):
            self.router.add_route(route2, self.handler)

    def test_transform_route_into_regexp(self):
        route = r'/path/{id}'
        expected_regexp_str = r'^/path/(?P<id>[a-zA-Z0-9_-]+)$'
        regexp_obj = self.router.build_route_regexp(route)
        self.assertEqual(expected_regexp_str, regexp_obj.pattern)

    def test_route_regexp_no_vars(self):
        route = Router.build_route_regexp(r'/path')
        path = r'/path'
        path_params = Router.match_path(route, path)
        self.assertDictEqual(path_params, {})

    def test_route_regexp_one_var(self):
        route = Router.build_route_regexp(r'/path/{var1}')
        path = r'/path/12'
        path_params = Router.match_path(route, path)
        self.assertDictEqual({'var1': '12'}, path_params)

    def test_route_regexp_multiple_vars(self):
        route = Router.build_route_regexp(r'/path/{var1}/edit/{var2}')
        path = r'/path/12/edit/name'
        path_params = Router.match_path(route, path)
        self.assertDictEqual(
            {'var1': '12', 'var2': 'name'},
            path_params)

    def test_add_multiple_routes(self):
        route = Router.build_route_regexp(r'/{var1}/{var2}/{var3}')
        path = r'/1/12/123'
        path_params = Router.match_path(route, path)
        self.assertDictEqual(
            {'var1': '1', 'var2': '12', 'var3': '123'},
            path_params)

    def test_raise_404(self):
        with self.assertRaises(NotFoundException):
            self.router.get_handler('/some-path')

    def test_inject_request_into_handler(self):
        route = r'/path'
        self.router.add_route(route, self.handler)
        wrapped_handler = self.router.get_handler(route)
        response = yield from wrapped_handler.handle('request')
        self.assertEqual(response, 'Body!')

    def test_update_request_path_params(self):
        class DummyRequest:
            def __init__(self):
                self.path_params = {}

        request = DummyRequest()
        route = r'/path/{id}'
        path = r'/path/12'
        self.router.add_route(route, self.handler)
        wrapped_handler = self.router.get_handler(path)
        response = yield from wrapped_handler.handle(request)
        self.assertTupleEqual(
            (request, ['12']),
            response)

    def test_route_precedence_matching(self):
        route1 = r'/'
        route2 = r'/welcome/{name}'
        path = '/welcome/bob'
        handler2 = lambda r, name: name
        self.router.add_routes({route1: self.handler, route2: handler2})
        wrapped_handler = self.router.get_handler(path)
        response = yield from wrapped_handler.handle('request')
        self.assertEqual(response, 'bob')


if __name__ == '__main__':
    t.main()
