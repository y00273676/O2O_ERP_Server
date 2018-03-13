#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import pyDes
import base64
import logging
import traceback
import datetime

from decimal import Decimal
from tornado import web
from control import ctrl
from lib import utils
from settings import ERR_MSG
from raven.contrib.tornado import SentryMixin
from tornado.options import options

DES = pyDes.des('DESCRYPT', pyDes.CBC, '\0\0\0\0\0\0\0\0', pad=None, padmode=pyDes.PAD_PKCS5)

class BaseHandler(web.RequestHandler, SentryMixin):

    def dict_args(self):
        _rq_args = self.request.arguments
        rq_args = dict([(k, _rq_args[k][0].decode()) for k in _rq_args])
        logging.info(rq_args)
        return rq_args

    def initialize(self):
        ctrl.pdb.close()

    def on_finish(self):
        ctrl.pdb.close()

    def json_format(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, Decimal):
            return ('%.2f' % obj)
        if isinstance(obj, bytes):
            return obj.decode()

    def has_argument(self, name):
        return name in self.request.arguments

    def options(self):
        self.send_json()

    def send_json(self, data={}, errcode=200, errmsg='', status_code=200):
        res = {
            'errcode': errcode,
            'errmsg': errmsg if errmsg else ERR_MSG.get(errcode, '异常错误')
        }
        res.update(data)

        if errcode > 200:
            logging.error(res)

        json_str = json.dumps(res, default=self.json_format)
        if options.debug:
            logging.info('%s, path: %s, arguments: %s, body: %s, response: %s' % (self.request.method, self.request.path, self.request.arguments, self.request.body, json_str))

        jsonp = self.get_argument('jsonp', '')
        if jsonp:
            jsonp = re.sub(r'[^\w\.]', '', jsonp)
            self.set_header('Content-Type', 'text/javascript; charet=UTF-8')
            json_str = '%s(%s)' % (jsonp, json_str)
        else:
            self.set_header('Content-Type', 'application/json')

        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.set_header('Access-Control-Allow-Methods', 'OPTIONS, GET, POST, PUT, DELETE')

        self.set_status(status_code)
        self.write(json_str)
        self.finish()

    def write_error(self, status_code=200, **kwargs):
        if 'exc_info' in kwargs:
            err_object = kwargs['exc_info'][1]
            traceback.format_exception(*kwargs['exc_info'])

            if isinstance(err_object, utils.APIError):
                err_info = err_object.kwargs
                self.send_json(**err_info)
                return

        self.send_json(status_code=500, errcode=50001)
        if not options.debug:
            self.captureException(**kwargs)

    def render_err(self, err_title='抱歉，出错了', err_msg='页面不存在'):
        self.render('error.tpl', err_title=err_title, err_msg=err_msg)

    def get_current_user(self):
        token = self.get_argument('token', '')

        if not token:
            return None

        try:
            tokens = DES.decrypt(base64.urlsafe_b64decode(token)).decode().split('|')
            phone = tokens[0]
            store_id = int(tokens[1])
        except:
            return None

        user = {
            'phone': phone,
            'store_id': store_id
        }
        return user

    def _login(self, store):
        account = str(store['phone'])
        store_id = str(store['store_id'])
        token = base64.urlsafe_b64encode(DES.encrypt('|'.join([account, store_id])))
        return token

    def _logout(self, token):
        self.current_user = None
