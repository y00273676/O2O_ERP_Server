#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

from raven import Client
from sqlalchemy.orm import class_mapper

from lib import utils

def model2dict(model):
    if not model:
        return {}
    fields = class_mapper(model.__class__).columns.keys()
    return dict((col, getattr(model, col)) for col in fields)

def model_to_dict(func):
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        return model2dict(ret)
    return wrap

def models_to_list(func):
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        return [model2dict(r) for r in ret]
    return wrap

def tuples_first_to_list(func):
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        return [item[0] for item in ret]
    return wrap

def filter_update_data(func):
    def wrap(*args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']
            data = dict([(key, value) for key, value in data.items() if value or value == 0])
            kwargs['data'] = data
        return func(*args, **kwargs)
    return wrap

def tuple_to_dict(func):
    def wrap(*args, **kwargs):
        ret = func(*args, **kwargs)
        return [dict(zip(i.keys(), i.values())) for i in ret]
    return wrap

def check_ua(func):
    def wrap(*args, **kw):
        self = args[0]
        ua = self.request.headers.get('User-Agent', '')
        if 'ThunderErp' not in ua:
            return self.render('error.tpl')
        return func(*args, **kw)
    return wrap

def access_limit_control(self):
    '''
    对修改操作进行频率检查及登录校验
    '''
    method = self.request.method.upper()

    if method not in ['POST', 'PUT']:
        return

    path_str = self.request.path
    arguments = self.request.arguments
    request_body_str = self.request.body.decode()
    arg_values = [key + ''.join(list(map(bytes.decode, arguments[key]))) for key in sorted(arguments.keys())]
    arg_str = ''.join(arg_values)

    sign_str = path_str + arg_str + request_body_str
    key = 'rate_' + hashlib.md5(sign_str.encode()).hexdigest()
    RATE_LIMIT = 3

    from control import ctrl

    if ctrl.rs.exists(key):
        raise utils.APIError(errcode=50001, errmsg='访问频率过高')
    ctrl.rs.set(key, 1, RATE_LIMIT)

def erp_auth(func):

    def wrap(*args, **kw):
        self = args[0]

        access_limit_control(self)

        user = self.current_user
        if user:
            return func(*args, **kw)

        raise utils.APIError(errcode=10002)

    return wrap


client = Client('https://781b50a7bc3148e2ae48e590b3bb7233:07dffa57c3c14738a54b23433d2abe37@sentry.ktvsky.com/23')
def try_script_error(func):

    def wrap(*args, **kw):
        try:
            func()
        except:
            client.captureException()

    return wrap
