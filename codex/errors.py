# -*- coding: utf-8 -*- 
# @Time : 2020/5/21 15:59
# @File : errors.py
import ujson

"""错误异常"""


class BaseError(Exception):
    code = 500
    msg = "Sorry, we make a mistake!"

    def __init__(self, msg):
        self.code = 1
        self.msg = msg

    def __repr__(self):
        return self.msg


class PermissionDeniedError(BaseError):
    def __init__(self, msg):
        self.code = 2
        self.msg = msg


class ParamsError(BaseError):
    def __init__(self, msg):
        self.code = 3
        self.msg = msg


class AuthError(BaseError):
    def __init__(self, msg):
        self.code = 4
        self.msg = msg


class LogicError(BaseError):
    def __init__(self, msg):
        self.code = 5
        self.msg = msg


class DBDataExistsError(BaseError):
    def __init__(self, msg):
        self.code = 6
        self.msg = msg


class UserExistsError(BaseError):
    def __init__(self, msg):
        self.code = 7
        self.msg = ujson.dumps(msg)


class OptionsError(BaseError):
    def __init__(self, msg):
        self.code = 8
        self.msg = msg


class RoleExistsError(BaseError):
    def __init__(self, msg):
        self.code = 9
        self.msg = msg


class CommonRemoveError(BaseError):
    def __init__(self, msg):
        self.code = 10
        self.msg = msg


class CommonInsertError(BaseError):
    def __init__(self, msg):
        self.code = 10
        self.msg = msg


class CommonUpdateError(BaseError):
    def __init__(self, msg):
        self.code = 10
        self.msg = msg


class CommonListError(BaseError):
    def __init__(self, msg):
        self.code = 10
        self.msg = msg


if __name__ == '__main__':
    pass
