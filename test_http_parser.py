import unittest as t
from textwrap import dedent

from http_connection import Request


class TestRequest(t.TestCase):
    def setUp(self):
        self.get_r = bytearray(
            dedent("""GET /test.html?test=1 HTTP/1.1\r\n\
                                          Content-Type: text\r\n\r\n"""),
            encoding='ascii')
        self.post_r = bytearray(dedent("""POST /test.html HTTP/1.1\r\n
                         Content-Type: application/x-www-form-urlencoded\r\n
                         Content-Length: 10\r\n\r\n
                         12=45&78=9"""), encoding='ascii')

    def test_get_parse(self):
        r = Request()
        r.parse(self.get_r)
        self.assertTrue(r.finished)
        self.assertEqual(r.path, b'/test.html')
        self.assertEqual(r.query_params, {b'test': [b'1']})
        self.assertEqual(r.headers, {'content-type': 'text'})

    def test_post_parse(self):
        r = Request()
        r.parse(self.post_r)
        self.assertTrue(r.finished)
        self.assertEqual(r.body_raw, bytearray(b'12=45&78=9'))
        self.assertEqual(r.body, {b'12': [b'45'], b'78': [b'9']})

if __name__ == '__main__':
    t.main()
