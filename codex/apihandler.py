# -*- coding: utf-8 -*- 
# @Time : 2020/5/21 15:15
# @File : apihandler.py
import functools
import ujson
import time
import traceback
from django.http import HttpResponseNotAllowed, HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.views.generic import View

from codex.basehandler import BaseHandler, Dict
from codex.errors import BaseError, LogicError, AuthError, ParamsError


class KPResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        data = ujson.dumps(data)
        super().__init__(content=data, **kwargs)
        self.setdefault('Cache-Control', 'no-cache')
        self.setdefault('Access-Control-Allow-Origin', '*')
        self.setdefault('Access-Control-Allow-Methods', 'POST, GET, HEAD, OPTIONS')
        self.setdefault('Access-Control-Max-Age', '1000')
        self.setdefault('Access-Control-Allow-Headers', '*')
        self.setdefault("Server", "kunpeng.brinte.cn")


class FileResponse(StreamingHttpResponse):
    def __init__(self, streaming_content=(), *args, **kwargs):
        file_name = kwargs.pop("file_name", "")
        size = kwargs.pop("size", "")
        super().__init__(*args, **kwargs)
        self.streaming_content = streaming_content
        self.setdefault('Cache-Control', 'no-cache')
        self.setdefault('Access-Control-Allow-Origin', '*')
        self.setdefault('Access-Control-Allow-Methods', 'POST, GET, HEAD, OPTIONS')
        self.setdefault('Access-Control-Max-Age', '1000')
        self.setdefault('Access-Control-Allow-Headers', '*')
        self.setdefault("Server", "kunpeng.brinte.cn")
        # self['Content-Type'] = 'application/octet-stream'
        self.setdefault('Content-Type', 'application/octet-stream')
        self.setdefault('File-Size', size)
        # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
        self.setdefault('Content-Disposition', 'attachment;filename="{}"'.format(file_name))


class LazySettings(object):
    def __init__(self):
        self.default = {
            'cookie_expire': 7 * 24 * 3600,
            'env': 'dev',
            'cache': False,
        }
        try:
            self.constants = __import__('constants')
        except ValueError:
            self.constants = None

    def __getattr__(self, item):
        return getattr(self.constants, item, self.default.get(item))


settings = LazySettings()


class APIHandler(View, BaseHandler):
    status_code = None

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.set_cookie = {}
        self.delete_cookie = []
        handler = getattr(self, request.method.lower(), None)
        if request.method.lower() in ['head', 'options']:
            # response = HttpResponse('')
            # response["Access-Control-Allow-Origin"] = "*"
            # response["Access-Control-Allow-Methods"] = "POST, GET, HEAD, OPTIONS"
            # response["Access-Control-Max-Age"] = "1000"
            # response["Access-Control-Allow-Headers"] = "*"
            return KPResponse({})
        if not callable(handler):
            return self.http_method_not_allowed()
        return self.api_wrapper(handler, *args, **kwargs)

    def http_method_not_allowed(self, *args, **kwargs):
        return HttpResponseNotAllowed(self._allowed_methods())

    def api_wrapper(self, func, *args, **kwargs):
        self.query_or_body = None
        self.ip = self.request.META.get('HTTP_X_REAL_IP') or self.request.META.get('HTTP_X_FORWARDED_FOR') \
                  or self.request.META.get('REMOTE_ADDR', '')
        self.host = self.request.META.get('HTTP_HOST', '')
        self.http_origin = self.request.META.get('HTTP_ORIGIN', '')
        code = 0
        data = {}
        message = 'success'
        st = time.time()
        try:
            data = func(*args, **kwargs)
        except ParamsError as e:
            code = e.code
            message = str(e)
            self.log('INFO', message)
        except AuthError as e:
            code = e.code
            message = str(e)
            self.log('INFO', message)
            ...
        except Exception as e:
            # TODO
            code = 1
            message = str(e)
            self.log('ERROR', message)
            # traceback.print_exc()
            raise e
        res = {'code': code, 'data': data, 'msg': message, 'cost': '{}ms'.format(round((time.time() - st) * 1000, 4))}
        response = KPResponse(
            res,
            content_type='application/json',
            status=self.status_code,
        )
        # response['Cache-Control'] = 'no-cache'
        # response["Access-Control-Allow-Origin"] = "*"
        # response["Access-Control-Allow-Methods"] = "POST, GET, HEAD, OPTIONS"
        # response["Access-Control-Max-Age"] = "1000"
        # response["Access-Control-Allow-Headers"] = "*"
        if self.set_cookie:
            for k, v in list(self.set_cookie.items()):
                response.set_cookie(k, v, expires=settings.cookie_expire, httponly=True)
        if self.delete_cookie:
            for k in self.delete_cookie:
                response.delete_cookie(k)
        return response

    @property
    def body(self):
        return Dict(ujson.loads(self.request.body)) if self.request.body else Dict({})

    @property
    def query(self):
        d = Dict(getattr(self.request, 'GET').items())
        d.update(getattr(self.request, 'POST').items())
        d.update(getattr(self.request, 'FILES').items())
        return d

    @property
    def input(self):
        if self.query_or_body is None:
            self.query_or_body = self.query or self.body
        return self.query_or_body

    # def super_query(self, input_params: tuple = None):
    #     query = {param: self.input.get(param, "") for param in input_params} if input_params else {}
    #     if self.request.user.get("role", "admin") != "super":
    #         query["current_company_uid"] = self.request.user.get("current_company_uid", "")
    #     if self.request.user.get("role", "editor") == "editor":
    #         query["username"] = self.request.user.get("username", "")
    #     return query


class JumpHandler(View, BaseHandler):

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.set_cookie = {}
        self.set_header = {}
        self.delete_cookie = []
        handler = getattr(self, request.method.lower(), None)
        if not callable(handler):
            return self.http_method_not_allowed()
        return self.jump_wrapper(handler, *args, **kwargs)

    def http_method_not_allowed(self, *args, **kwargs):
        return HttpResponseNotAllowed(self._allowed_methods())

    def jump_wrapper(self, func, *args, **kwargs):
        self.query_or_body = None
        self.ip = self.request.META.get('HTTP_X_REAL_IP') or self.request.META.get('HTTP_X_FORWARDED_FOR') \
                  or self.request.META.get('REMOTE_ADDR', '')
        self.host = self.request.META.get('HTTP_HOST', '')
        self.http_origin = self.request.META.get('HTTP_ORIGIN', '')
        try:
            data = func(*args, **kwargs)
        except AuthError as e:
            data = '/404.html'
            self.log('INFO', str(e))
        except BaseError as e:
            data = '/404.html'
            self.log('ERROR', str(e), exc_info=True)
        except Exception as e:
            data = '/404.html'
            self.log('ERROR', str(e), exc_info=True)
        response = HttpResponseRedirect(data)
        parse = self.urlparse(data)
        if self.set_cookie:
            for k, v in list(self.set_cookie.items()):
                response.set_cookie(k, v, expires=settings.cookie_expire, httponly=True, domain=parse.netloc or None)
        if self.delete_cookie:
            for k in self.delete_cookie:
                response.delete_cookie(k)
        if self.set_header:
            for k, v in self.set_header.items():
                response[k] = v
        response['Access-Control-Allow-Credentials'] = "true"
        if parse.netloc:
            response['Access-Control-Allow-Origin'] = 'http://' + parse.netloc
        return response

    @property
    def body(self):
        return Dict(ujson.loads(self.request.body)) if self.request.body else Dict({})

    @property
    def query(self):
        d = Dict(iter(list(getattr(self.request, self.request.method).items())))
        d.update(iter(list(getattr(self.request, 'FILES').items())))
        return d

    @property
    def input(self):
        if self.query_or_body is None:
            self.query_or_body = self.query or self.body
        return self.query_or_body


def need_params(*params, **type_params):
    def dec(func):

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            for arg in params:
                if getattr(self.input, arg, None) is None:
                    raise LogicError('Need Params:%s' % arg)
            for k, _type in type_params.items():
                if getattr(self.input, k) is None:
                    raise LogicError('Need Params:%s' % k)
                if not isinstance(getattr(self.input, k), _type):
                    raise LogicError('Params "%s" type should be %s' % (k, _type))
            return func(self, *args, **kwargs)

        return wrapper

    return dec


if __name__ == '__main__':
    pass
