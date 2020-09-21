# -*- coding: utf-8 -*- 
# @Time : 2020/5/25 9:35
# @File : role.py

from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from codex.apihandler import KPResponse
from codex.basehandler import BaseHandler
from codex.cachehandler import cache

""""中间件定义，自定义的中间件请在settings中添加"""


def get_user(request, user):
    if not hasattr(request, '_cached_user'):
        request._cached_user = RequestUser(user)
    return request._cached_user


class RequestUser(BaseHandler):
    role = 'anonymous'  # 角色名
    available = False  # 逻辑删除

    def __init__(self, user):
        if user:
            self.user_init(user)

    @classmethod
    def get(cls, key, default=None):
        return cls.__dict__.get(key, default)

    @classmethod
    def set(cls, key, value):
        setattr(cls, key, value)

    @classmethod
    def delete(cls, keys: list):
        setattr(cls, "role", "anonymous")
        setattr(cls, "available", False)
        for item in keys:
            if getattr(cls, item, None):
                delattr(cls, item)

    @classmethod
    def __getattr__(cls, item):
        return cls.__dict__.get(item, None)

    @classmethod
    def user_init(cls, user):
        pass

class RequestUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 校验token， 其中带有user信息
        token = request.headers.get('Authorization', '') or request.COOKIES.get('Authorization')
        user_dict = cache.get(token) if token else None
        # 正常则将用户信息和权限，符合AnonymousUser形式
        request.user = SimpleLazyObject(lambda: get_user(request, user_dict))
        # request.user = get_user(request, user_dict)
        # print(request.user)


class TokenMiddleware(MiddlewareMixin):
    # enforcer = casbin.Enforcer("auth_path/restful_model.conf", "auth_path/restful_policy.csv")

    # enforcer = casbin.Enforcer("auth_path/restful_model.conf", adapter)
    enforcer = None
    # enforcer.enable_auto_save(True)
    # enforcer = MyCoreEnforcer("auth_path/restful_model.conf", adapter)

    def process_request(self, request):
        """登陆验证"""
        if not self.check_permission(request):
            return KPResponse({'code': 2, 'data': None, 'msg': "无权限操作!"}, content_type='application/json')
        # print(request.path, request.body)

    def m_load_policy(self, request):
        """reloads the policy from file/database."""

        self.enforcer.model.clear_policy()
        self.enforcer.adapter.load_policy(self.enforcer.model, request=request)

        self.enforcer.model.print_policy()
        if self.enforcer.auto_build_role_links:
            self.enforcer.build_role_links()

    def check_permission(self, request):
        # Customize it based on your authentication method.
        path = request.path
        method = request.method
        role = request.user.role
        app = request.headers.get("App", "oauth")

        #  第一种
        self.m_load_policy(request)
        #  第二种  风险，有线程数据安全问题， 具体自个去看源码分析。
        # self.enforcer.adapter.parse_request(request)
        # self.enforcer.load_policy()
        print(self.enforcer.model.model["p"]["p"].policy)
        print(self.enforcer.enforce(role, path, method, app), role, path, method, app)
        return self.enforcer.enforce(role, path, method, app)


if __name__ == '__main__':
    pass
