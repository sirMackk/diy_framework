"""
Module response for parsing bytes objects into HTTP requests.
All of the functions in here operate on byte buffers and modify them
instead of working on copies.
"""

import re
import json
from urllib import parse

from .exceptions import BadRequestException


CRLF = b'\x0d\x0a'
SEPARATOR = CRLF + CRLF
HTTP_VERSION = b'1.1'
SUPPORTED_METHODS = [
    'GET',
    'POST',
]
REQUEST_LINE_REGEXP = re.compile(br'[a-z]+ [a-z0-9.?_\[\]=&-\\]+ http/%s' %
                                 (HTTP_VERSION), flags=re.IGNORECASE)


def parse_into(request, buffer):
    """
    Main function of the module - it incrementally parses a bytes object
    and stores the information in request. First it attempts to parse the
    request line and http headers. Based on that, it then attempts to
    parse the body if applicable. This function expected to be called
    with the same request and buffer objects throughout an HTTP request's
    life cycle.

    :param request: an object that will store parsed data. Must expose the
        Request interface.
    :param buffer: a bytes objects. It will copied, the copy will be
        modified during parsing.
    :return: A bytes object that is the modified copy of the buffer param.
    """
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
        clear_buffer(_buffer)
        request.finished = True
    return _buffer


def has_body(headers):
    """
    :param headers: A dict-like object.
    """
    return 'content-length' in headers


def can_parse_request_line(buffer):
    """
    Uses a regular expression to determine whether buffer contains
    something that looks like an HTTP request line.

    :param buffer: a bytes like object.
    """
    return REQUEST_LINE_REGEXP.match(buffer) is not None


def can_parse_headers(buffer):
    """
    Checks to see if buffer contains the CRLFCRFL sequence, which
    signals the end of headers in an HTTP request.

    :param buffer: a bytes like object.
    """
    return SEPARATOR in buffer


def parse_request_line(buffer):
    """
    Parses the buffer to extract information from the request line.

    :param buffer: a bytes like object.
    :return: A typle of HTTP method, path, and query params.
    """
    request_line = buffer.split(CRLF)[0].decode('utf-8')
    method, raw_path = request_line.split(' ')[:2]
    method = method.upper()
    if method not in SUPPORTED_METHODS:
        raise BadRequestException('{} method not supported'.format(method))

    path, query_params = parse_query_params(raw_path)
    return method, path, query_params


def parse_query_params(raw_path):
    """
    Parses a string to extract the path and any URL params.

    :param raw_path: string representation of an HTTP path ie. /path?key=val.
    :return: path string and a dict of URL params in the form of {key: [val]}.
    """
    url_obj = parse.urlparse(raw_path)
    path = url_obj.path
    query_params = parse.parse_qs(url_obj.query)
    return path, query_params


def parse_headers(buffer):
    """
    Parses the buffer and creates a dict of header: value. Collapses
    duplicate headers into one.

    :param buffer: a bytes like object.
    :return: Dict of headers.
    """
    headers_end = buffer.index(SEPARATOR)
    headers_iter = (line for line in buffer[:headers_end].split(CRLF) if line)
    headers = {}
    for line in headers_iter:
        header, value = [i.strip() for i in line.strip().split(b':')[:2]]
        header = header.decode('utf-8').lower()
        headers[header] = value.decode('utf-8')
    return headers


def can_parse_body(headers, buffer):
    """
    Checks whether a request's headers signal a body to parse.

    :param headers: A dict of header: value pairs.
    :param buffer: a bytes object.
    :return: Boolean.
    """
    content_length = int(headers.get('content-length', '0'))
    return 'content-length' in headers and len(buffer) == content_length


def parse_body(headers, buffer):
    """
    Parses a requests body according to the Content-Type header.
    Uses application/x-www-form-urlencoded by default.

    :param headers: a dict of header: value pairs.
    :param buffer: a bytes objects.
    :return: A tuple of the raw_body bytes and a parsed, utf-8-encoded,
        dict representing the body.
    """
    body_raw = buffer[:]
    content_type = headers.get(
        'content-type', 'application/x-www-form-urlencoded')
    parser = get_body_parser(content_type)
    body = parser(body_raw)
    utf_8_body = byte_kv_to_utf8(body)
    return body_raw, utf_8_body


def get_body_parser(content_type):
    """
    Selects the correct parses to use for parsing a request's body.

    :param content_type: a string representing the request's content type.
    :return: function that expects a string input and outputs parsed text.
    """
    if content_type == 'application/x-www-form-urlencoded':
        return parse.parse_qs
    elif content_type == 'application/json':
        return json.dumps


def byte_kv_to_utf8(kv):
    """
    :param kv: a dict of byte keys:values.
    :return: a dict of utf-8 keys:values.
    """
    return {
        k.decode('utf-8'): [val.decode('utf-8') for val in v]
        for k, v in kv.items()}


def remove_request_line(buffer):
    """
    Deletes the request line from the buffer.

    :param buffer: a bytes object.
    """
    first_line_end = buffer.index(CRLF)
    del buffer[:first_line_end]


def remove_intro(buffer):
    """
    Deletes everything up to the CRLFCRLF sequence - the request
    line as well as the headers.

    :param buffer: a bytes object.
    """
    request_boundry = buffer.index(SEPARATOR)
    del buffer[:request_boundry + len(SEPARATOR)]


def clear_buffer(buffer):
    """
    Clears the buffer.

    :param buffer: a bytes object.
    """

    del buffer[:]
