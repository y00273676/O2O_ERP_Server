#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import time
import datetime

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler
from tornado.httputil import url_concat
from tornado.options import options
from tornado.ioloop import IOLoop
from settings import PAY_MD, ORDER_STATE, BILL_PAY_STATE


WX_PAY_URL = 'http://pay.ktvsky.com/{paytype}'
if options.debug:
    WX_PAY_URL = 'http://pay.stage.ktvsky.com/{paytype}'


class PrepayHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        预付
        '''
        try:
            args = json.loads(self.request.body.decode())
            room_id = int(args['room_id'])
            prepay = int(args['prepay'])
            pay_md = int(args['pay_md'])
            order_no = args['order_no']

            assert(pay_md in PAY_MD.values())
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        bill = ctrl.order.order_prepay_ctl(self.current_user['store_id'], order_no, room_id, prepay, pay_md)

        FILTER = (
            {'id': 'bill_id'},
            'bill_no',
            'room_id',
            'money',
            'pay_md',
            'update_time'
        )

        data = {
            'detail': utils.dict_filter(bill, FILTER)
        }
        self.send_json(data)


class SeqTimeHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        续时
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            minute = int(args['minute'])
            order_no = args['order_no']
            describe = args['describe']
            pay_md = int(args.get('pay_md', 1))
            rate = int(args.get('rate', 100))
            money = int(args.get('money', 0))
            real_money = int(args.get('real_money', 0))

            pay_data = {
                'describe': describe,
                'pay_md': pay_md,
                'rate': rate,
                'money': money,
                'real_money': real_money
            }

            assert(pay_md in PAY_MD.values())
            assert(rate == 100)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']
        phone = self.current_user['phone']

        bill = ctrl.order.seq_time_ctl(store_id, phone, order_no, rt_id, room_id, minute, pay_data)

        FILTER = (
            {'id': 'bill_id'},
            'bill_no',
            'room_id',
            'update_time'
        )

        data = {
            'detail': utils.dict_filter(bill, FILTER)
        }
        self.send_json(data)


class SeqPackHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        续套餐
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            pack_id = int(args['pack_id'])
            order_no = args['order_no']
            describe = args['describe']
            pay_md = int(args.get('pay_md', 1))
            rate = int(args.get('rate', 100))
            money = int(args.get('money', 0))
            real_money = int(args.get('real_money', 0))

            pay_data = {
                'describe': describe,
                'pay_md': pay_md,
                'rate': rate,
                'money': money,
                'real_money': real_money
            }

            assert(pay_md in PAY_MD.values())
            assert(rate == 100)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        bill = ctrl.order.seq_pack_ctl(self.current_user['store_id'], order_no, rt_id, room_id, pack_id, pay_data)

        FILTER = (
            {'id': 'bill_id'},
            'bill_no',
            'room_id',
            'update_time'
        )

        data = {
            'detail': utils.dict_filter(bill, FILTER)
        }

        self.send_json(data)


class ProductHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取已点的酒水列表
        '''
        try:
            order_no = int(self.get_argument('order_no'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        products = ctrl.order.get_order_products_ctl(self.current_user['store_id'], order_no)

        FILTER = (
            'room_id',
            'product_id',
            'pack_id',
            'count',
            'unit',
            'name',
            'price',
            'money',
            'pay_state',
            'md',
            'create_time'
        )

        data = {
            'list': [utils.dict_filter(product, FILTER) for product in products]
        }

        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        点单
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            order_no = args['order_no']
            describe = args['describe']
            pay_md = int(args.get('pay_md', 1))
            rate = int(args.get('rate', 100))
            money = int(args.get('money', 0))
            real_money = int(args.get('real_money', 0))

            pay_data = {
                'describe': describe,
                'pay_md': pay_md,
                'rate': rate,
                'money': money,
                'real_money': real_money
            }

            packs = []
            products = []
            for arg in args['products']:
                product_id = int(arg['product_id'])
                count = int(arg['count'])
                products.append({
                    'product_id': product_id,
                    'count': count
                })
            for arg in args['packs']:
                pack_id = int(arg['pack_id'])
                count = int(arg['count'])
                packs.append({
                    'pack_id': pack_id,
                    'count': count
                })

            assert(pay_md in PAY_MD.values())
            assert(rate == 100)
            assert(packs or products)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        FILTER = (
            {'id': 'bill_id'},
            'bill_no',
            'room_id',
            'update_time'
        )

        bill = ctrl.order.order_products_packs_ctl(self.current_user['store_id'], order_no, rt_id, room_id, products, packs, pay_data)

        data = {
            'detail': utils.dict_filter(bill, FILTER)
        }

        self.send_json(data)


class BackProductHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        退单
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            order_no = args['order_no']
            money = int(args['money'])
            pay_md = int(args.get('pay_md', 1))
            describe = args.get('describe', '')

            products = []
            for arg in args['products']:
                product_id = int(arg['product_id'])
                count = int(arg['count'])
                products.append({
                    'product_id': product_id,
                    'count': count
                })

            assert(pay_md in PAY_MD.values())
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        bill = ctrl.order.back_order_products_ctl(self.current_user['store_id'], order_no, rt_id, room_id, money, pay_md, describe, products)

        FILTER = (
            {'id': 'bill_id'},
            'bill_no',
            'room_id',
            'money',
            'pay_md',
            'update_time'
        )

        data = {
            'detail': utils.dict_filter(bill, FILTER)
        }

        self.send_json(data)


class DetailHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        账单明细
        '''
        try:
            order_no = int(self.get_argument('order_no'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        order = ctrl.order.get_order_detail_ctl(self.current_user['store_id'], order_no)

        FILTER = (
            'order_no',
            'room_id',
            'room_name',
            'prepay',
            'pay_md',
            'pay_type',
            'minute',
            'st',
            'ed',
            'state',
            'describe',
            'update_time',
            'bills'
        )

        data = {
            'detail': utils.dict_filter(order, FILTER)
        }

        self.send_json(data)


class CheckoutHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        结账
        '''
        try:
            args = json.loads(self.request.body.decode())
            order_no = args['order_no']
            money = int(args['money'])
            real_money = int(args['real_money'])
            pay_md = int(args.get('pay_md', 1))
            describe = args['describe']

        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.order.checkout_order_ctl(self.current_user['store_id'], order_no, money, real_money, pay_md, describe)

        data = {
            'detail': dict(order_no=order_no, bill_id=0)
        }
        self.send_json(data)


class CloseHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        关台
        '''
        try:
            order_no = int(self.get_argument('order_no'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.order.close_order_ctl(self.current_user['store_id'], order_no)

        self.send_json()


class WriteOfHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        手动核销, bill_id=0, 则是对整个订单
        '''
        try:
            args = json.loads(self.request.body.decode())
            order_no = int(args['order_no'])
            bill_id = int(args.get('bill_id', 0))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.order.write_of_order_bills_ctl(self.current_user['store_id'], order_no, bill_id)

        self.send_json()


class PayHandler(BaseHandler):

    @erp_auth
    async def get(self):
        try:
            order_no = int(self.get_argument('order_no'))
            bill_id = int(self.get_argument('bill_id', '0'))
            paytype = self.get_argument('paytype', 'wx')

            assert paytype in ('wx', 'ali')
            store_id = self.current_user['store_id']
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        res = await ctrl.order.pay_query_ctl(store_id, order_no, bill_id, paytype)
        self.send_json(dict(pay_result=res))

    @erp_auth
    async def post(self):
        try:
            args = json.loads(self.request.body.decode())
            order_no = int(args.get('order_no', 0))
            bill_id = int(args.get('bill_id', 0))
            auth_code = args['auth_code']
            paytype = args.get('paytype', 'wx')

            store_id = self.current_user['store_id']
            assert paytype in ('wx', 'ali')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        res = await ctrl.order.post_pay_ctl(store_id, order_no, bill_id, auth_code, paytype)
        if 'order' not in res:
            raise utils.APIError(errcode=10003)

        is_room = False
        if bill_id:
            bill = ctrl.order.get_bill_ctl(store_id, bill_id)
            if bill['bill_no'].startswith('KT'):
                is_room = True

        order_state = 0
        if utils.is_success_pay(paytype, res):
            order_state = 1
            ctrl.order.success_pay_ctl(store_id, order_no, bill_id, paytype, is_room=is_room)

        data = dict(pay_id=res['order'])
        if bill_id:
            if order_state:
                data.update({'pay_state': BILL_PAY_STATE['pay']})
            ctrl.order.dummy_update_bill_ctl(store_id, order_no, bill_id, data)
        else:
            if order_state:
                data.update({'state': ORDER_STATE['finish']})
            ctrl.order.update_order_ctl(store_id, order_no, data)

        if not order_state:
            IOLoop.current().add_timeout(time.time()+10, ctrl.order.pay_query_ctl, store_id, order_no, bill_id, paytype, loop=15)

        self.send_json(dict(pay_result=res))


class RepayHandler(BaseHandler):

    @erp_auth
    async def post(self):
        try:
            args = json.loads(self.request.body.decode())
            order_no = args['order_no']
            bill_id = int(args.get('bill_id'))
            rate = int(args.get('rate', 100))
            money = int(args['money'])
            real_money = int(args['real_money'])
            pay_md = int(args.get('pay_md', 1))
            describe = args['describe']
            store_id = self.current_user['store_id']

            assert(rate == 100)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'rate': rate,
            'money': money,
            'real_money': real_money,
            'pay_md': pay_md,
            'describe': describe,
            'pay_id': '',
        }
        ctrl.order.dummy_update_bill_ctl(store_id, order_no, bill_id, data)
        if pay_md in (PAY_MD['cash'], PAY_MD['pos']):
            ctrl.order.after_success_bill_ctl(store_id, order_no, bill_id)

        self.send_json({
            'detail': {
                'order_no': order_no,
                'bill_id': bill_id
            }
        })


class BillHandler(BaseHandler):

    @erp_auth
    def put(self):
        try:
            args = json.loads(self.request.body.decode())
            order_no = args['order_no']
            bill_id = args['bill_id']
            store_id = self.current_user['store_id']
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.order.cancel_bill_ctl(store_id, order_no, bill_id)
        self.send_json()

