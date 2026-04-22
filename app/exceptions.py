class AppException(Exception):
    pass


class UserAlreadyExistsError(AppException):
    pass


class InvalidCredentialsError(AppException):
    pass


class FormNotFoundError(AppException):
    pass


class AccessDeniedError(AppException):
    pass


class InvalidAnswersError(AppException):
    pass
