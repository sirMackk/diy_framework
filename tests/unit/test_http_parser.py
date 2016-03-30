import unittest as t

import http_parser
from http_utils import Request

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

    def test_short_get_parse(self):
        r = Request()
        short_get = bytearray('gEt / http/1.1\r\n\r\n', encoding='utf-8')
        http_parser.parse_into(r, short_get)
        self.assertTrue(r.finished)
        self.assertEqual(r.path, '/')
        self.assertDictEqual(r.headers, {})

    def test_get_parse(self):
        r = Request()
        http_parser.parse_into(r, self.get_r)
        self.assertTrue(r.finished)
        self.assertEqual(r.path, '/test.html')
        self.assertEqual(r.query_params, {b'test': [b'1']})
        self.assertEqual(r.headers, {'content-type': 'text'})

    def test_post_parse(self):
        r = Request()
        http_parser.parse_into(r, self.post_r)
        self.assertTrue(r.finished)
        self.assertEqual(r.body_raw, bytearray(b'12=45&78=9'))
        self.assertEqual(r.body, {b'12': [b'45'], b'78': [b'9']})

if __name__ == '__main__':
    t.main()
