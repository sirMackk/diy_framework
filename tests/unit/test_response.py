import unittest as t

from http_utils import Response


class TestResponse(t.TestCase):
    def setUp(self):
        self.body = '<b>Response</b>'
        self.r = Response(code=200, body=self.body)

    def test_byte_response(self):
        byte_r = self.r.to_bytes()
        self.assertIsInstance(byte_r, bytes)

    def test_correct_content_length(self):
        byte_r = self.r.to_bytes()
        self.assertEqual(
            self.r.headers['Content-Length'], len(self.body))
        self.assertIn(b'Content-Length', byte_r)

    def test_general_response_structure(self):
        from re import MULTILINE, match
        byte_r = self.r.to_bytes()
        match_obj = match(
            br'[a-zA-Z0-9/.\r\n:\s-]+\r\n\r\n' + self.body.encode(),
            byte_r,
            flags=MULTILINE)
        self.assertIsNotNone(match_obj)

if __name__ == '__main__':
    t.main()
