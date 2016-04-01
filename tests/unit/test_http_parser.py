import unittest as t

from diy_framework import http_parser
from diy_framework.http_utils import Request

# add more edge case tests


class TestHTTPParser(t.TestCase):
    def setUp(self):
        self.get_r = bytearray(
            ('GET /test.html?test=1 HTTP/1.1\r\n'
             'Content-Type: text\r\n\r\n'),
            encoding='ascii')
        self.post_r = bytearray(
            ('POST /test.html HTTP/1.1\r\n'
             'Content-Type: application/x-www-form-urlencoded\r\n'
             'Content-Length: 10\r\n\r\n12=45&78=9'), encoding='ascii')

        self.r = Request()

    def test_short_get_parse(self):
        short_get = bytearray('gEt / http/1.1\r\n\r\n', encoding='utf-8')
        http_parser.parse_into(self.r, short_get)
        self.assertTrue(self.r.finished)
        self.assertEqual(self.r.path, '/')
        self.assertDictEqual(self.r.headers, {})

    def test_get_parse(self):
        http_parser.parse_into(self.r, self.get_r)
        self.assertTrue(self.r.finished)
        self.assertEqual(self.r.path, '/test.html')
        self.assertEqual(self.r.query_params, {'test': ['1']})
        self.assertEqual(self.r.headers, {'content-type': 'text'})

    def test_post_parse(self):
        http_parser.parse_into(self.r, self.post_r)
        self.assertTrue(self.r.finished)
        self.assertEqual(self.r.body_raw, bytearray(b'12=45&78=9'))
        self.assertEqual(self.r.body, {'12': ['45'], '78': ['9']})

    def test_uniform_method(self):
        short_get = bytearray(
            b'gEt / http/1.1\r\n\r\nContent-Type: text/plain')
        http_parser.parse_into(self.r, short_get)
        self.assertEqual(self.r.method, 'GET')



if __name__ == '__main__':
    t.main()
