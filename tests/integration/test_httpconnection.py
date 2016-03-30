import asyncio
from random import randint
import unittest as t
from unittest.mock import patch, MagicMock


import requests

import http_parser
from http_connection import HTTPConnection
from router import Router


class TestHTTPConnection(t.TestCase):
    def setUp(self):
        pass

    def test_empty_get_request(self):
        pass

    @t.skip('')
    def test_url_params_get_request(self):
        pass

    @t.skip('')
    def test_post_request(self):
        pass

    @t.skip('')
    def test_request_timeout(self):
        pass

    @t.skip('')
    def test_response_timeout(self):
        pass


if __name__ == '__main__':
    t.main()
