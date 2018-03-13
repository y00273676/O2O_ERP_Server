try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import json
import pyDes
import base64
import logging
import datetime
import tornado.testing
from tornado.httputil import url_concat
from tornado.options import options, define

try:
    # python -m tests --case=wxpay
    define('case', default='', help='assign test case')
    define('debug', default=True, help='assign test case')
except:
    pass

import app

DES = pyDes.des('DESCRYPT', pyDes.CBC, '\0\0\0\0\0\0\0\0', pad=None, padmode=pyDes.PAD_PKCS5)

def current_time_str():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

class AsyncHTTPTestCase(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return app.Application()

    def get(self, url, **kwargs):
        if 'params' in kwargs and isinstance(kwargs['params'], dict):
            url = url_concat(url, kwargs.pop('params'))
        return self.my_fetch(url, method='GET', **kwargs)

    def post(self, url, **kwargs):
        # if 'body' in kwargs and isinstance(kwargs['body'], dict):
        #     kwargs['body'] = urlencode(kwargs['body'])
        body = kwargs.get('body', {})
        body = json.dumps(body)
        return self.my_fetch(url, method='POST', body=body)

    def put(self, url, **kwargs):
        body = kwargs.get('body', {})
        body = json.dumps(body)
        return self.my_fetch(url, method='PUT', body=body)

    def delete(self, url, **kwargs):
        if 'params' in kwargs and isinstance(kwargs['params'], dict):
            url = url_concat(url, kwargs.pop('params'))
        return self.my_fetch(url, method='DELETE', **kwargs)

    def gen_token(self, phone, store_id):
        return base64.urlsafe_b64encode(DES.encrypt('|'.join([str(phone), str(store_id)]))).decode()

    def my_fetch(self, url, **kwargs):
        '''
        log every api call info (method, path, args, result)
        '''
        res = self.fetch(url, **kwargs)
        method = kwargs.pop('method')
        logging.info('%s, path: %s, args: %s, result: %s'%(method, url, kwargs, json.loads(res.body.decode())))
        return res

