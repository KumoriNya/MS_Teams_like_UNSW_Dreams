from werkzeug.exceptions import HTTPException

class AccessError(HTTPException):
    code = 403
    message = 'Access Error'

class InputError(HTTPException):
    code = 400
    message = 'Input Error'

class DuplicateError(HTTPException):
    code = 505
    message = 'Duplicated message'
