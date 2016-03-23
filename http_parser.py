import re
import json
from urllib import parse


CRLF = b'\x0d\x0a'
SEPARATOR = CRLF + CRLF
HTTP_VERSION = b'1.1'
SUPPORTED_METHODS = [
    b'GET',
    b'POST',
]
REQUEST_LINE_REGEXP = re.compile(br'(%s) [A-Z0-9.?_\[\]=&-\\]+ http/%s' % (
    b'|'.join(SUPPORTED_METHODS), HTTP_VERSION), flags=re.IGNORECASE)


def parse_into(request, buffer):
    _buffer = buffer[:]
    if not request.method and can_parse_request_line(_buffer):
        (request.method, request.path,
         request.query_params) = parse_request_line(_buffer)
        remove_request_line(_buffer)

    if not request.headers and can_parse_headers(_buffer):
        request.headers = parse_headers(_buffer)
        if not has_body(request.headers):
            request.finished = True

        remove_intro(_buffer)

    if not request.finished and can_parse_body(request.headers, _buffer):
        request.body_raw, request.body = parse_body(request.headers, _buffer)
        remove_body(_buffer)
        request.finished = True
    return _buffer


def has_body(headers):
    return 'content-length' in headers


def can_parse_request_line(buffer):
    return REQUEST_LINE_REGEXP.match(buffer) is not None


def can_parse_headers(buffer):
    return SEPARATOR in buffer


def parse_request_line(buffer):
    request_line = buffer.split(CRLF)[0]
    method, raw_path = request_line.split(b' ')[:2]
    path, query_params = parse_query_params(raw_path)
    return method, path, query_params


def parse_query_params(raw_path):
    url_obj = parse.urlparse(raw_path)
    path = url_obj.path
    query_params = parse.parse_qs(url_obj.query)
    return path, query_params


def parse_headers(buffer):
    headers_end = buffer.index(SEPARATOR)
    headers_iter = (line for line in buffer[:headers_end].split(CRLF) if line)
    headers = {}
    for line in headers_iter:
        header, value = line.strip().split(b' ')[:2]
        header = header.decode('utf-8').lower()[:-1]
        headers[header] = value.decode('utf-8')
    return headers


def can_parse_body(headers, buffer):
    content_length = int(headers.get('content-length', '0'))
    return 'content-length' in headers and len(buffer) == content_length


def parse_body(headers, buffer):
    body_raw = buffer[:]
    content_type = headers.get('content-type', '')
    parser = get_body_parser(content_type)
    body = parser(body_raw)
    return body_raw, body


def get_body_parser(content_type):
    if content_type == 'application/x-www-form-urlencoded':
        return parse.parse_qs
    elif content_type == 'application/json':
        return json.dumps


def remove_request_line(buffer):
    first_line_end = buffer.index(CRLF)
    del buffer[:first_line_end + len(CRLF)]


def remove_intro(buffer):
    request_boundry = buffer.index(SEPARATOR)
    del buffer[:request_boundry + len(SEPARATOR)]


def remove_body(buffer):
    del buffer[:]
