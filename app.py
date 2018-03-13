#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import uuid
import base64

from tornado import web
from tornado.options import options
from lib import uimodules, uimethods
from tornado.httpserver import HTTPServer
from raven.contrib.tornado import AsyncSentryClient


STATIC_PATH = os.path.join(sys.path[0], 'static')
URLS = [
    (r'android\.ktvsky\.com',
        (r'/(.*\.txt)', web.StaticFileHandler, {'path': STATIC_PATH}),
        (r'/store/code', 'handler.store.CodeHandler'),
        (r'/store/verify', 'handler.store.VerifyHandler'),
        (r'/store/signup', 'handler.store.SignupHandler'),
        (r'/store/login', 'handler.store.LoginHandler'),
        (r'/store/account', 'handler.store.AccoutHandler'),
        (r'/store/logout', 'handler.store.LogoutHandler'),
        (r'/store/reset', 'handler.store.ResetHandler'),
        (r'/room/type', 'handler.room.TypeHandler'),
        (r'/room/ip', 'handler.room.IPHandler'),
        (r'/room/fee', 'handler.room.FeeHandler'),
        (r'/room/pack', 'handler.room.PackHandler'),
        (r'/pack', 'handler.pack.PackHandler'),
        (r'/pack/product', 'handler.pack.ProductHandler'),
        (r'/cate', 'handler.cate.CateHandler'),
        (r'/cate/product', 'handler.cate.CateProductHandler'),
        (r'/calc/time', 'handler.calc.ByTimeHandler'),
        (r'/calc/pack', 'handler.calc.ByPackHandler'),
        (r'/open/time', 'handler.open.ByTimeHandler'),
        (r'/open/pack', 'handler.open.ByPackHandler'),
        (r'/order/prepay', 'handler.order.PrepayHandler'),
        (r'/order/seq/time', 'handler.order.SeqTimeHandler'),
        (r'/order/seq/pack', 'handler.order.SeqPackHandler'),
        (r'/order/product', 'handler.order.ProductHandler'),
        (r'/order/back/product', 'handler.order.BackProductHandler'),
        (r'/order/detail', 'handler.order.DetailHandler'),
        (r'/order/checkout', 'handler.order.CheckoutHandler'),
        (r'/order/close', 'handler.order.CloseHandler'),
        (r'/order/write/of', 'handler.order.WriteOfHandler'),
        (r'/order/pay', 'handler.order.PayHandler'),
        (r'/order/repay', 'handler.order.RepayHandler'),
        (r'/order/bill', 'handler.order.BillHandler'),
        (r'/trade/stat/revenue', 'handler.trade.StatRevenueHandler'),
        (r'/trade/stat/product', 'handler.trade.StatProductHandler'),
        (r'/trade/stat/pack', 'handler.trade.StatPackHandler'),
        (r'/trade/order', 'handler.trade.OrderHandler'),
        (r'/trade/order/bill', 'handler.trade.OrderBillHandler')
    )
]

class Application(web.Application):

    def __init__(self):
        settings = {
            'xsrf_cookies': False,
            'compress_response': True,
            'debug': options.debug,
            'ui_modules': uimodules,
            'ui_methods': uimethods,
            'static_path': STATIC_PATH,
            'cookie_secret': base64.b64encode(uuid.uuid3(uuid.NAMESPACE_DNS, 'android').bytes),
            'sentry_url': 'https://781b50a7bc3148e2ae48e590b3bb7233:07dffa57c3c14738a54b23433d2abe37@sentry.ktvsky.com/23' if not options.debug else ''
        }
        web.Application.__init__(self, **settings)
        for spec in URLS:
            host = '.*$'
            handlers = spec[1:]
            self.add_handlers(host, handlers)


def run():
    app = Application()
    app.sentry_client = AsyncSentryClient(app.settings['sentry_url'])
    http_server = HTTPServer(app, xheaders=True)
    http_server.listen(options.port)
    print('Running on port %d' % options.port)

