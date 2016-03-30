class DiyFrameworkException(Exception):
    pass


class NotFoundException(DiyFrameworkException):
    code = 404


class BadRequestException(DiyFrameworkException):
    code = 400


class DuplicateRoute(DiyFrameworkException):
    pass


class TimeoutException(DiyFrameworkException):
    code = 500
