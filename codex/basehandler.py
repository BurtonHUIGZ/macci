# -*- coding: utf-8 -*- 
# @Time : 2020/5/21 15:17
# @File : basehandler.py
import copy
import json
import random
from urllib import parse
import base64
import datetime
import hashlib
import os
import subprocess
import time
import uuid
import zlib
import ujson
import re

from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.db.transaction import atomic

from codex.errors import BaseError
from macci.settings import logger


class LazySettings(object):
    def __init__(self):
        self.default = {
            'cookie_expire': 10 * 24 * 3600,
            'env': 'dev',
            'cache': False,
        }
        try:
            self.constants = __import__('constants')
        except ValueError:
            self.constants = None

    def __getattr__(self, item):
        return getattr(self.constants, item.upper(), self.default.get(item))


settings = LazySettings()


class BaseHandler(object):
    @staticmethod
    def tms2str(x, f="%Y-%m-%d %H:%M:%S"):
        """毫秒时间戳转化为年月日时分秒"""
        return time.strftime(f, time.localtime(int(x / 1000)))

    @staticmethod
    def wi_fi(x):
        """信号强度值单位转换"""
        if isinstance(x, str):
            return "N/A"
        return "%s dBm" % x

    @staticmethod
    def tms2hms(x):
        """毫秒时间转换时分秒"""
        x = int(x / 1000)
        h = x // 3600
        m = x // 60 % 60
        s = x % 60
        return "%s时%s分%s秒" % (h, m, s) if h > 0 else "%s分%s秒" % (m, s) if m > 0 else "%s秒" % s

    @classmethod
    def uuid_hex(cls):
        return uuid.uuid4().hex

    @classmethod
    def hash_md5(cls, d: dict):
        return hashlib.md5(json.dumps(d).encode()).hexdigest()

    @classmethod
    def generate_hash_uuid(cls, limit=None):
        u = uuid.uuid4().hex
        if limit:
            u = u[:limit]
        return u

    @classmethod
    def get_datetime_now(cls):
        return datetime.datetime.now()

    @classmethod
    def get_std_timestamp(cls):
        return cls.get_datetime_now().strftime('%Y%m%d%H%M%S%f')[:-3]

    @classmethod
    def get_random_str(cls):
        H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        num = random.randint(5, 10)
        salt = ''
        for i in range(num):
            salt += random.choice(H)
        return salt

    @classmethod
    def get_timestamps(cls, lever: float = 1000, integer: bool = True):
        """时间戳"""
        return int(time.time() * lever) if integer else time.time() * lever

    @classmethod
    def time_create(cls, t, f='%Y-%m-%d %H:%M:%S'):
        return t.strftime(f)

    @classmethod
    def timestamps2str(cls, t, f="%Y-%m-%d %H:%M:%S"):
        return time.strftime(f, time.localtime(t if isinstance(t, (int, float)) else float(t)))

    @classmethod
    def strptime(cls, t, f='%Y-%m-%d %H:%M:%S'):
        return datetime.datetime.strptime(t, f)

    @classmethod
    def getnow_strtime(cls, f='%Y_%m%d_%H_%M%S'):
        return datetime.datetime.now().strftime(f)

    @classmethod
    def page_serializer(cls, data: list, count: int, page: int):
        paginator = Paginator(data, count)
        try:
            result_data = paginator.page(page)
            # todo: 注意捕获异常
        except PageNotAnInteger:
            # 如果请求的页数不是整数, 返回第一页。
            result_data = paginator.page(1)
        except InvalidPage:
            # 如果请求的页数不存在, 重定向页面
            return {'error': '找不到页面的内容'}
        except EmptyPage:
            # 如果请求的页数不在合法的页数范围内，返回结果的最后一页。
            result_data = paginator.page(paginator.num_pages)
        # result_data = data[start: end]
        return {"result": result_data.object_list, "total_count": len(data)}

    @classmethod
    def str2tms(cls, t, f='%Y-%m-%d %H:%M:%S'):  # float
        return time.mktime(time.strptime(t, f))

    @classmethod
    def get_datetime_utcnow(cls):
        return datetime.datetime.utcnow()

    @classmethod
    def from_timestamp(cls, timestamp):
        return datetime.datetime.fromtimestamp(timestamp)

    @classmethod
    def to_timestamp(cls, t):
        return time.mktime(t.timetuple())

    @classmethod
    def round(cls, n, d=0):
        f = 10 ** d
        return int(n * f + 0.5) / f

    @classmethod
    def sha1(cls, string):
        return hashlib.sha1(string.encode('UTF-8') if isinstance(string, str) else string).hexdigest()

    @classmethod
    def b64encode(cls, bytestring):
        return base64.b64encode(bytestring.encode('UTF-8') if isinstance(bytestring, str) else bytestring)

    @classmethod
    def b64decode(cls, bytestring):
        return base64.b64decode(bytestring.encode('UTF-8') if isinstance(bytestring, str) else bytestring)

    @classmethod
    def dumps(cls, obj, compress=False, ensure_ascii=True):
        if compress:
            compress_obj = zlib.compressobj()
            compress_obj = compress_obj.compress(ujson.dumps(obj).encode('utf-8')) + compress_obj.flush()
            return base64.b64encode(compress_obj).decode('utf-8')
        else:
            return ujson.dumps(obj, ensure_ascii=ensure_ascii)

    @classmethod
    def loads(cls, string, default=None, decompress=False):
        if not string:
            return default
        if decompress:
            decompress_obj = zlib.decompressobj()
            decompress_obj = decompress_obj.decompress(
                base64.b64decode(string.encode('utf-8'))) + decompress_obj.flush()
            return ujson.loads(decompress_obj)
        else:
            return ujson.loads(string)

    @classmethod
    def timedelta(cls, **kwargs):
        return datetime.timedelta(**kwargs)

    @classmethod
    def pipe(cls, args, input_string=None, shell=True):
        if isinstance(args, list):
            p = subprocess.Popen(
                args,
                stdin=None if input_string is None else subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell)
            out, err = p.communicate(None if input_string is None else input_string.encode('utf-8'))
            exit_code = p.returncode
            if exit_code != 0:
                cmd = args[0].split(' ')[0]
                raise IOError(f'{cmd} exited with non-zero code {exit_code}. error: {err}')
            p.kill()
            p.terminate()
            return out
        elif isinstance(args, str):
            with os.popen(args, mode="r") as p:
                return p.read()
        raise TypeError

    @classmethod
    def wkpdf(cls, url, orientation=None, size=None, external=None, stop_slow_scripts=False):
        cmd = 'wkhtmltopdf -B 0 -L 0 -R 0 -T 0'
        if orientation:
            cmd += ' -O %s' % orientation
        if size:
            cmd += ' -s %s' % size
        cmd += ' --window-status ready '
        if not stop_slow_scripts:
            cmd += ' --no-stop-slow-scripts '
        if external:
            cmd += ' ' + external + ' '
        cmd += ' "%s" -' % url
        return cls.pipe([cmd])

    @classmethod
    def wkimg(cls, url, external=None, stop_slow_scripts=False):
        cmd = 'wkhtmltoimage --window-status ready '
        if not stop_slow_scripts:
            cmd += ' --no-stop-slow-scripts '
        if external:
            cmd += external
        cmd += ' "%s" -' % url
        return cls.pipe([cmd])

    @classmethod
    def urlparse(cls, url):
        return parse.urlparse(url)

    @classmethod
    def urlencode(cls, data, **kwargs):
        return parse.urlencode(data, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        try:
            level = level.lower()
            message = repr(msg)
            if hasattr(self, 'request'):
                message = repr(getattr(self, 'request')) + ' ' + repr(msg)
            if level in ('debug', 'info', 'warning', 'error', 'critical'):
                func = getattr(logger, level)
                func(message, *args, **kwargs)
        except Exception as e:
            print(e)

    @staticmethod
    def dict_fetchall(cursor):
        desc = cursor.description
        return [
            dict(list(zip([col[0] for col in desc], row)))
            for row in cursor.fetchall()
        ]

    @staticmethod
    def check_email(mail_str):
        p = re.compile(r'^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$')
        return p.match(mail_str)


class ModelHandler(BaseHandler):
    # model wrapper
    base_model = None
    base_error = BaseError

    def __init__(self, model):
        self.model = model
        self.cache = {}

    def __getattr__(self, item):
        if item.startswith('get_') and hasattr(self.model, item[4:]):
            value = getattr(self.model, item[4:], None)
            if isinstance(value, datetime.datetime):
                value = self.time_create(value)
            elif isinstance(value, datetime.date):
                value = value.strftime('%Y-%m-%d')
            elif isinstance(value, type(None)):
                value = ""
            return lambda: value
        else:
            return self.__getattribute__(item)

    def set(self, **kwargs):
        for k, v in list(kwargs.items()):
            setattr(self.model, k, v)
        self.model.save()

    def get_own(self, *args):
        data = {}
        for a in args:
            data[a] = getattr(self, 'get_' + a)()
        return data

    def flush(self, using=None):
        manager = self.base_model.objects
        if using:
            manager = manager.using(using)
        self.model = manager.get(id=self.get_id())

    @staticmethod
    def execute_raw(raw, params=()):
        from django.db import connection
        cursor = connection.cursor()
        if params:
            affected_rows = cursor.execute(raw, params)
        else:
            affected_rows = cursor.execute(raw)
        cursor.close()
        return affected_rows

    @staticmethod
    def query_raw(raw, params=()):
        from django.db import connection
        cursor = connection.cursor()
        if params:
            cursor.execute(raw, params)
        else:
            cursor.execute(raw)
        data = cursor.fetchall()
        cursor.close()
        return data

    @staticmethod
    def query_dict_raw(raw, params=()):
        from django.db import connection
        cursor = connection.cursor()
        if params:
            cursor.execute(raw, params)
        else:
            cursor.execute(raw)
        data = BaseHandler.dict_fetchall(cursor)
        cursor.close()
        return data

    @classmethod
    def get_by_id(cls, _id, using=None):
        return cls.get_by_query(_using=using, id=_id)

    @classmethod
    def get_by_uid(cls, uid):
        return cls.get_by_query(uid=uid)

    @classmethod
    def get_by_query(cls, _using=None, **query):
        try:
            manager = cls.base_model.objects
            if _using:
                manager = manager.using(_using)
            return cls(manager.get(**query))
        except cls.base_model.DoesNotExist:
            raise cls.base_error(cls.__name__ + 'DoesNotExist')
        except cls.base_model.MultipleObjectsReturned:
            raise cls.base_error(cls.__name__ + 'MultipleObjectsReturned')

    @classmethod
    def filter_by_query(cls, _using=None, *args, **kwargs):
        manager = cls.base_model.objects
        if _using:
            manager = manager.using(_using)
        return manager.filter(*args, **kwargs)

    @classmethod
    def get_list(cls, *args, **kwargs):
        data = list()
        for s in cls.base_model.objects.filter(**kwargs):
            model = cls(s)
            data.append({a: getattr(model, 'get_' + a)() for a in args})
        return data

    @classmethod
    def create(cls, **kwargs):
        return cls(cls.base_model.objects.create(**kwargs))

    @classmethod
    def get_or_create(cls, _using=None, **kwargs):
        manager = cls.base_model.objects
        if _using:
            manager = manager.using(_using)
        model, _ = manager.get_or_create(**kwargs)
        return cls(model)

    @staticmethod
    @atomic
    def batch_save(instances):
        for ins in instances:
            ins.save()

    @property
    def objects(self):
        return self.base_model.objects

    @classmethod
    def get_all_fields(cls, exclude=[]):
        if cls.base_model:
            return [field.name for field in cls.base_model._meta.fields if field.name not in exclude]


class Dict(dict):
    def __getattr__(self, item):
        resp = self.get(item, None)
        if isinstance(resp, dict):
            resp = Dict(resp)
        return resp

    def __setattr__(self, key, value):
        self[key] = value

    def __deepcopy__(self, memodict={}):
        return Dict((copy.deepcopy(k, memodict), copy.deepcopy(v, memodict)) for k, v in self.items())

    def __copy__(self):
        return Dict(self.items())


if __name__ == '__main__':
    print(BaseHandler.timestamps2str(1590666182, ))
    pass
