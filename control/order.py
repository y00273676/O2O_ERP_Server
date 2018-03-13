#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import when
import datetime
import pickle
import logging

from lib import utils
from tornado.ioloop import IOLoop
from tornado.options import options
from tornado.httputil import url_concat
from settings import A_DAY, PAY_TYPE, ROOM_TYPE, SERVICE_TYPE, BILL_PRO_MD, ORDER_STATE, BILL_PAY_STATE, BILL_MD, PAY_MD

BILL_FILTER = (
    {'id': 'bill_id'},
    'bill_no',
    'money',
    'real_money',
    'rate',
    'pay_md',
    'pay_state',
    'service_type',
    'describe',
    'update_time',
    'list'
)
BILL_RO_FILTER = (
    'fee_id',
    'pack_id',
    'st',
    'ed',
    'minute',
    'money',
    'md',
    'name',
    'price',
    'update_time',
    'list'
)
BILL_PRO_FILTER = (
    'product_id',
    'pack_id',
    'count',
    'unit',
    'name',
    'price',
    'money',
    'md',
    'update_time',
    'list'
)
PRODUCT_FILTER = (
    {'id': 'product_id'},
    'store_id',
    'cate_id',
    'name',
    'pic',
    'price',
    'unit',
    'spec',
    'stock',
    'discount',
    'state',
    'order',
    'count',
    'update_time'
)

WX_PAY_URL = 'http://pay.ktvsky.com/{paytype}'
if options.debug:
    WX_PAY_URL = 'http://pay.stage.ktvsky.com/{paytype}'


class OrderCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.order = ctrl.pdb.order

    def __getattr__(self, name):
        return getattr(self.order, name)

    def get_order_key(self, store_id, order_no):
        return 't_order_%s_%s' % (store_id, order_no)

    def get_using_order_key(self, store_id, room_id):
        return 't_using_order_%s_%s' % (store_id, room_id)

    def get_order_bill_ids_key(self, store_id, order_id):
        return 't_order_bill_ids_%s_%s' % (store_id, order_id)

    def get_bill_key(self, store_id, bill_id):
        return 't_bill_%s_%s' % (store_id, bill_id)

    def get_order_bill_room_ids_key(self, store_id, order_id):
        return 't_order_bill_room_ids_%s_%s' % (store_id, order_id)

    def get_bill_room_key(self, store_id, br_id):
        return 't_bill_room_%s_%s' % (store_id, br_id)

    def get_order_bill_product_ids_key(self, store_id, order_id):
        return 't_order_bill_product_ids_%s_%s' % (store_id, order_id)

    def get_bill_product_key(self, store_id, bp_id):
        return 't_bill_product_%s_%s' % (store_id, bp_id)

    def check_repeat_update_order_or_bill(self, store_id, order_no, bill_id):
        '''订单貌似不需要，账单需要限制重复，比如续时需要改动订单和包房的时间'''
        key = 't_forbid_repeat_%s_%s_%s' % (store_id, order_no, bill_id)
        if self.ctrl.rs.exists(key):
            return True
        return False

    def forbid_repeat_update_order_or_bill(self, store_id, order_no, bill_id):
        key = 't_forbid_repeat_%s_%s_%s' % (store_id, order_no, bill_id)
        self.ctrl.rs.set(key, 1, 60*60)

    def get_using_orders(self, store_id, room_ids=[]):
        if not room_ids:
            return []

        multi_key = [self.get_using_order_key_ctl(store_id, room_id) for room_id in room_ids]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_order = dict(zip(multi_key, cached))
        miss_ids = [room_id for room_id in room_ids if multi_order[self.get_using_order_key_ctl(store_id, room_id)] is None]
        if not miss_ids:
            return [multi_order[self.get_using_order_key_ctl(store_id, room_id)] for room_id in room_ids]

        miss_order_list = self.order.get_using_orders(store_id, miss_ids)
        miss_ids = [miss_order['room_id'] for miss_order in miss_order_list]
        miss_multi_key = [self.get_using_order_key_ctl(store_id, miss_id) for miss_id in miss_ids]
        miss_order = dict(zip(miss_multi_key, miss_order_list))

        if miss_order:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_order_encode = dict((key, pickle.dumps(miss_order[key])) for key in miss_order)
            pl.mset(miss_order_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_order.update(miss_order)
        return [multi_order[self.get_using_order_key_ctl(store_id, room_id)] for room_id in room_ids if self.get_using_order_key_ctl(store_id, room_id) in multi_order]

    def get_using_order(self, store_id, room_id):
        orders = self.get_using_orders_ctl(store_id, [room_id])
        if not orders:
            return {}
        return orders[-1]

    def disable_order(self, store_id, order_no, room_id):
        self.update_order_ctl(store_id, order_no, {
            'state': ORDER_STATE['invalid']
        })
        key = self.get_using_order_key_ctl(store_id, room_id)
        self.ctrl.rs.delete(key)

    def get_bills(self, store_id, bill_ids=[]):
        if not bill_ids:
            return []

        multi_key = [self.get_bill_key_ctl(store_id, bill_id) for bill_id in bill_ids]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_bill = dict(zip(multi_key, cached))
        miss_ids = [bill_id for bill_id in bill_ids if multi_bill[self.get_bill_key_ctl(store_id, bill_id)] is None]
        if not miss_ids:
            return [multi_bill[self.get_bill_key_ctl(store_id, bill_id)] for bill_id in bill_ids]

        miss_bill_list = self.order.get_bills(store_id, miss_ids)
        miss_ids = [miss_bill['id'] for miss_bill in miss_bill_list]
        miss_multi_key = [self.get_bill_key_ctl(store_id, miss_id) for miss_id in miss_ids]
        miss_bill = dict(zip(miss_multi_key, miss_bill_list))

        if miss_bill:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_bill_encode = dict((key, pickle.dumps(miss_bill[key])) for key in miss_bill)
            pl.mset(miss_bill_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_bill.update(miss_bill)
        return [multi_bill[self.get_bill_key_ctl(store_id, bill_id)] for bill_id in bill_ids if self.get_bill_key_ctl(store_id, bill_id) in multi_bill]

    def get_bill(self, store_id, bill_id):
        bills = self.get_bills_ctl(store_id, [bill_id])
        if not bills:
            return {}
        return bills[0]

    def get_order_bill_ids(self, store_id, order_id):
        key = self.get_order_bill_ids_key_ctl(store_id, order_id)
        bill_ids = self.ctrl.rs.lrange(key, 0, -1)

        if bill_ids:
            return [int(bill_id) for bill_id in bill_ids]

        bill_ids = self.order.get_order_bill_ids(store_id, order_id)
        if not bill_ids:
            return bill_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *bill_ids).expire(key, A_DAY).execute()
        return bill_ids

    def get_order_bills(self, store_id, order_id):
        bill_ids = self.get_order_bill_ids_ctl(store_id, order_id)
        if not bill_ids:
            return []
        bills = self.get_bills_ctl(store_id, bill_ids)
        return bills

    def get_bills_room(self, store_id, br_ids=[]):
        if not br_ids:
            return []

        multi_key = [self.get_bill_room_key_ctl(store_id, br_id) for br_id in br_ids]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_bill = dict(zip(multi_key, cached))
        miss_ids = [br_id for br_id in br_ids if multi_bill[self.get_bill_room_key_ctl(store_id, br_id)] is None]
        if not miss_ids:
            return [multi_bill[self.get_bill_room_key_ctl(store_id, br_id)] for br_id in br_ids]

        miss_bill_list = self.order.get_bills_room(store_id, miss_ids)
        miss_ids = [miss_bill['id'] for miss_bill in miss_bill_list]
        miss_multi_key = [self.get_bill_room_key_ctl(store_id, miss_id) for miss_id in miss_ids]
        miss_bill = dict(zip(miss_multi_key, miss_bill_list))

        if miss_bill:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_bill_encode = dict((key, pickle.dumps(miss_bill[key])) for key in miss_bill)
            pl.mset(miss_bill_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_bill.update(miss_bill)
        return [multi_bill[self.get_bill_room_key_ctl(store_id, br_id)] for br_id in br_ids if self.get_bill_room_key_ctl(store_id, br_id) in multi_bill]

    def get_order_bill_room_ids(self, store_id, order_id):
        key = self.get_order_bill_room_ids_key_ctl(store_id, order_id)
        br_ids = self.ctrl.rs.lrange(key, 0, -1)

        if br_ids:
            return [int(br_id) for br_id in br_ids]

        br_ids = self.order.get_order_bill_room_ids(store_id, order_id)
        if not br_ids:
            return br_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *br_ids).expire(key, A_DAY).execute()
        return br_ids

    def get_order_bills_room(self, store_id, order_id):
        br_ids = self.get_order_bill_room_ids_ctl(store_id, order_id)
        if not br_ids:
            return []
        bills = self.get_bills_room_ctl(store_id, br_ids)
        return bills

    def get_bills_product(self, store_id, bp_ids=[]):
        if not bp_ids:
            return []

        multi_key = [self.get_bill_product_key_ctl(store_id, bp_id) for bp_id in bp_ids]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_bill = dict(zip(multi_key, cached))
        miss_ids = [bp_id for bp_id in bp_ids if multi_bill[self.get_bill_product_key_ctl(store_id, bp_id)] is None]
        if not miss_ids:
            return [multi_bill[self.get_bill_product_key_ctl(store_id, bp_id)] for bp_id in bp_ids]

        miss_bill_list = self.order.get_bills_product(store_id, miss_ids)
        miss_ids = [miss_bill['id'] for miss_bill in miss_bill_list]
        miss_multi_key = [self.get_bill_product_key_ctl(store_id, miss_id) for miss_id in miss_ids]
        miss_bill = dict(zip(miss_multi_key, miss_bill_list))

        if miss_bill:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_bill_encode = dict((key, pickle.dumps(miss_bill[key])) for key in miss_bill)
            pl.mset(miss_bill_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_bill.update(miss_bill)
        return [multi_bill[self.get_bill_product_key_ctl(store_id, bp_id)] for bp_id in bp_ids if self.get_bill_product_key_ctl(store_id, bp_id) in multi_bill]

    def get_order_bill_product_ids(self, store_id, order_id):
        key = self.get_order_bill_product_ids_key_ctl(store_id, order_id)
        bp_ids = self.ctrl.rs.lrange(key, 0, -1)

        if bp_ids:
            return [int(bp_id) for bp_id in bp_ids]

        bp_ids = self.order.get_order_bill_product_ids(store_id, order_id)
        if not bp_ids:
            return bp_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *bp_ids).expire(key, A_DAY).execute()
        return bp_ids

    def get_order_bills_product(self, store_id, order_id):
        bp_ids = self.get_order_bill_product_ids_ctl(store_id, order_id)
        if not bp_ids:
            return []
        bills = self.get_bills_product_ctl(store_id, bp_ids)
        return bills

    def get_orders(self, store_id, order_nos=[]):
        if not order_nos:
            return []

        multi_key = [self.get_order_key_ctl(store_id, order_no) for order_no in order_nos]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_order = dict(zip(multi_key, cached))
        miss_nos = [order_no for order_no in order_nos if multi_order[self.get_order_key_ctl(store_id, order_no)] is None]
        if not miss_nos:
            return [multi_order[self.get_order_key_ctl(store_id, order_no)] for order_no in order_nos]

        miss_order_list = self.order.get_orders(store_id, tuple(miss_nos))
        miss_nos = [miss_order['order_no'] for miss_order in miss_order_list]
        miss_multi_key = [self.get_order_key_ctl(store_id, miss_no) for miss_no in miss_nos]
        miss_order = dict(zip(miss_multi_key, miss_order_list))

        if miss_order:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_order_encode = dict((key, pickle.dumps(miss_order[key])) for key in miss_order)
            pl.mset(miss_order_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_order.update(miss_order)
        return [multi_order[self.get_order_key_ctl(store_id, order_no)] for order_no in order_nos if self.get_order_key_ctl(store_id, order_no) in multi_order]

    def get_order(self, store_id, order_no):
        order = self.get_orders_ctl(store_id, [order_no])[0]
        return order

    def update_order(self, store_id, order_no, data):
        self.order.update_order(store_id, order_no, data=data)
        key = self.get_order_key_ctl(store_id, order_no)
        self.ctrl.rs.delete(key)

    def dummy_update_bill(self, store_id, order_no, bill_id, data={}):
        assert data
        self.order.update_bill(store_id, bill_id, data)
        key = self.get_bill_key_ctl(store_id, bill_id)
        self.ctrl.rs.delete(key)

    def add_order(self, store_id, room_id, st, ed, money, real_money, pay_type, describe):
        order_no = utils.gen_order_no()
        minute = utils.minute_distance(st, ed)
        pay_state = utils.get_pay_state(pay_type)

        data = {
            'order_no': order_no,
            'room_id': room_id,
            'st': st,
            'ed': ed,
            'minute': minute,
            'pay_type': pay_type,
            'describe': describe,
            'state': ORDER_STATE['invalid']
        }

        order = self.order.add_order(store_id, data)
        return order

    def add_bill(self, store_id, room_id, pay_type, order_id, money, real_money, rate, pay_md, describe='', prefix='KT', service_type=SERVICE_TYPE['room'], extra={}, order_no=''):
        '''
        点[帐]单，如果所属订单是现结，则需支付，账单状态按支付结果
                            落单后结，则都是未支付
        '''
        if pay_type==PAY_TYPE['current']:
            pay_state = utils.get_bill_pay_state(pay_md)
        else:
            pay_state = BILL_PAY_STATE['unpay']

        bill_no = utils.gen_bill_no(prefix)

        data = {
            'order_id': order_id,
            'bill_no': bill_no,
            'room_id': room_id,
            'pay_state': pay_state,
            'describe': describe,
            'service_type': service_type,
            'money': money,
            'real_money': real_money if real_money else money,
            'rate': rate,
            'pay_md': pay_md,
            'extra': json.dumps(extra)
        }

        bill = self.order.add_bill(store_id, data)
        key = self.get_order_bill_ids_key_ctl(store_id, order_id)
        self.ctrl.rs.delete(key)

        is_room = True if bill_no.startswith('KT') else False
        if pay_state == BILL_PAY_STATE['pay']:     # 添加的账单是已结的
            self.after_success_bill_ctl(store_id, order_no, bill['id'], is_room=is_room)

        return bill

    def update_bill(self, store_id, bill_id, money, pay_md):
        self.order.update_bill(store_id, bill_id, {
            'money': money,
            'pay_md': pay_md,
            'pay_state': BILL_PAY_STATE['pay']
        })
        key = self.get_bill_key_ctl(store_id, bill_id)
        self.ctrl.rs.delete(key)

    def add_prepay_bill(self, store_id, room_id, order_id, order_no, prepay, pay_md):
        bill_no = utils.gen_bill_no('YF')
        pay_state = utils.get_bill_pay_state(pay_md)
        bill = self.order.add_bill(store_id, {
            'order_id': order_id,
            'bill_no': bill_no,
            'room_id': room_id,
            'money': prepay,
            'real_money': prepay,
            'pay_md': pay_md,
            'pay_state': pay_state,
            'service_type': SERVICE_TYPE['prepay']
        })
        key = self.get_order_bill_ids_key_ctl(store_id, order_id)
        self.ctrl.rs.delete(key)

        if pay_state == BILL_PAY_STATE['pay']:
            self.after_success_bill_ctl(store_id, order_no, bill['id'])
        return bill

    def add_back_bill(self, store_id, room_id, order_id, order_no, money, pay_md, describe):
        # 现结的单，退单的账单状态设置为已付
        order = self.get_order_ctl(store_id, order_no)
        pay_state = BILL_PAY_STATE['unpay']
        if order['pay_type'] == PAY_TYPE['current']:
            pay_state = BILL_PAY_STATE['pay']

        bill_no = utils.gen_bill_no('TD')
        data = {
            'order_id': order_id,
            'bill_no': bill_no,
            'room_id': room_id,
            'money': -(abs(money)),
            'pay_md': pay_md,
            'describe': describe,
            'pay_state': pay_state,
            'service_type': SERVICE_TYPE['back']
        }
        bill = self.order.add_bill(store_id, data)
        key = self.get_order_bill_ids_key_ctl(store_id, order_id)
        self.ctrl.rs.delete(key)

        return bill

    def add_bill_room(self, store_id, phone, rt_id, room_id, st, ed, order_id, bill_id, fee_bills):
        tbs = []
        for bill in fee_bills:
            tbs.append({
                'order_id': order_id,
                'bill_id': bill_id,
                'room_id': room_id,
                'fee_id': bill['fee_id'],
                'st': bill['st'],
                'ed': bill['ed'],
                'minute': bill['minute'],
                'money': bill['money'],
                'md': BILL_MD['time']
            })
        self.order.add_bill_room(store_id, tbs)
        key = self.get_order_bill_room_ids_key_ctl(store_id, order_id)
        self.ctrl.rs.delete(key)

    def add_bill_room_by_pack(self, store_id, order_id, bill_id, room_id, pack_id, st, ed, minute, money):
        self.order.add_bill_room(store_id, [{
            'order_id': order_id,
            'bill_id': bill_id,
            'room_id': room_id,
            'pack_id': pack_id,
            'st': st,
            'ed': ed,
            'minute': minute,
            'money': money,
            'md': BILL_MD['pack']
        }])
        key = self.get_order_bill_room_ids_key_ctl(store_id, order_id)
        self.ctrl.rs.delete(key)

    def add_bill_product(self, store_id, order_id, products, packs):
        self.order.add_bill_product(store_id, products, packs)

        key = self.get_order_bill_product_ids_key_ctl(store_id, order_id)
        self.ctrl.rs.delete(key)

    def check_order(self, store_id, order_no):
        order = self.get_order_ctl(store_id, order_no)

        if not order or order['state'] not in [ORDER_STATE['using']]:
            raise utils.APIError(errcode=50001, errmsg='未开台')

        return order

    def order_prepay(self, store_id, order_no, room_id, prepay, pay_md):
        order = self.check_order_ctl(store_id, order_no)

        if order['pay_type'] not in [PAY_TYPE['poster']]:
            raise utils.APIError(errcode=50001, errmsg='落单后结才能预付')

        # if order['money']-order['prepay'] < prepay:
        #     raise utils.APIError(errcode=50001, errmsg='预付金额大于订单金额')

        bill = self.add_prepay_bill_ctl(store_id, room_id, order['id'], order_no, prepay, pay_md)
        return bill

    def check_room_valid(self, store_id, rt_id, room_id):
        room = self.ctrl.room.get_room_ctl(room_id)

        if not room:
            raise utils.APIError(errcode=50001, errmsg='包房无效')

        if room['room_type'] not in [ROOM_TYPE['using'], ROOM_TYPE['timeout']]:
            raise utils.APIError(errcode=50001, errmsg='未开台')

        return room

    def seq_time(self, store_id, phone, order_no, rt_id, room_id, minute, pay_data):
        pay_md = pay_data['pay_md']
        money = pay_data['money']
        real_money = pay_data['real_money']
        rate = pay_data['rate']
        describe = pay_data['describe']

        self.check_room_valid_ctl(store_id, rt_id, room_id)

        order = self.check_order_ctl(store_id, order_no)
        ed = utils.future_time_by_minute(order['ed'], minute)
        # total = order['minute'] + minute
        fee_bills = self.ctrl.calc.by_time_ctl(store_id, phone, rt_id, room_id, order['ed'], ed)

        order_id = order['id']
        bill = self.add_bill_ctl(store_id, room_id, order['pay_type'], order_id, money, real_money, rate, pay_md, describe, 'XS', order_no=order['order_no'], extra={'minute': minute})
        self.add_bill_room_ctl(store_id, phone, rt_id, room_id, order['ed'], ed, order_id, bill['id'], fee_bills)

        if order['pay_type']==PAY_TYPE['poster'] or pay_md in (PAY_MD['cash'], PAY_MD['pos']):
            self.after_success_bill_ctl(store_id, order_no, bill['id'])
        return bill

    def check_pack(self, pack_id):
        pack = self.ctrl.pack.get_pack_ctl(pack_id)

        if not pack:
            raise utils.APIError(errcode=50001, errmsg='该套餐不存在')

        if not utils.is_valid_pack(pack):
            raise utils.APIError(errcode=50001, errmsg='该套餐已下架')

        return pack

    def seq_pack(self, store_id, order_no, rt_id, room_id, pack_id, pay_data):
        pay_md = pay_data['pay_md']
        money = pay_data['money']
        real_money = pay_data['real_money']
        rate = pay_data['rate']
        describe = pay_data['describe']

        self.check_room_valid_ctl(store_id, rt_id, room_id)

        pack = self.check_pack_ctl(pack_id)
        order = self.check_order_ctl(store_id, order_no)

        minute = pack['hour'] * 60
        ed = utils.future_time_by_minute(order['ed'], minute, format='YYYY.MM.DD HH:mm')
        total = minute + order['minute']

        bill = self.add_bill_ctl(store_id, room_id, order['pay_type'], order['id'], money, real_money, rate, pay_md, describe, 'XS', order_no=order['order_no'], extra={'minute': minute})
        self.add_bill_room_by_pack_ctl(store_id, order['id'], bill['id'], room_id, pack_id, order['ed'], ed, minute, pack['price'])

        if order['pay_type']==PAY_TYPE['poster'] or pay_md in (PAY_MD['cash'], PAY_MD['pos']):
            self.after_success_bill_ctl(store_id, order_no, bill['id'])
        return bill

    def back_order_products(self, store_id, order_no, rt_id, room_id, money, pay_md, describe, products):
        self.check_room_valid_ctl(store_id, rt_id, room_id)

        order = self.check_order_ctl(store_id, order_no)
        order_id = order['id']

        self.update_order_money_ctl(store_id, order, -money, -money)
        bill = self.add_back_bill_ctl(store_id, room_id, order_id, order_no, money, pay_md, describe)
        bill_id = bill['id']

        products = self.get_products_info_ctl(products, order_id, bill_id, room_id)
        [p.update({ 'count': -1*p['count'], 'money': -1*p['money'] }) for p in products]
        self.add_bill_product_ctl(store_id, order_id, products, [])
        return bill

    def update_order_money(self, store_id, order, money, real_money=0, data={}):
        pay_type = order['pay_type']
        order_no = order['order_no']
        pay_state = utils.get_pay_state(pay_type)

        if pay_state == BILL_PAY_STATE['pay']:
            total_money = order['money'] + money
            total_real_money = order['real_money'] + real_money
            data.update({
                'money': total_money,
                'real_money': total_real_money
            })

        if data:
            self.update_order_ctl(store_id, order_no, data)

    def order_products_packs(self, store_id, order_no, rt_id, room_id, products, packs, pay_data):
        pay_md = pay_data['pay_md']
        money = pay_data['money']
        real_money = pay_data['real_money']
        rate = pay_data['rate']
        describe = pay_data['describe']

        self.check_room_valid_ctl(store_id, rt_id, room_id)

        order = self.check_order_ctl(store_id, order_no)
        order_id = order['id']

        bill = self.add_bill_ctl(store_id, room_id, order['pay_type'], order_id, money, real_money, rate, pay_md, describe, 'DD', SERVICE_TYPE['product'], order_no=order['order_no'])
        bill_id = bill['id']

        products = self.get_products_info_ctl(products, order_id, bill_id, room_id)
        packs = self.get_packs_info_ctl(packs, order_id, bill_id, room_id)
        self.add_bill_product_ctl(store_id, order_id, products, packs)

        if order['pay_type']==PAY_TYPE['poster'] or pay_md in (PAY_MD['cash'], PAY_MD['pos']):
            self.after_success_bill_ctl(store_id, order_no, bill['id'])

        return bill

    def get_products_info(self, products, order_id, bill_id, room_id):
        if not products:
            return products

        pids = [product['product_id'] for product in products]
        pdts = self.ctrl.pack.get_products_ctl(pids)
        pdts = dict((pdt['id'], pdt) for pdt in pdts)

        for product in products:
            count = product['count']
            product_id = product['product_id']
            price = pdts[product_id]['price']
            money = price * count
            product.update({
                'order_id': order_id,
                'bill_id': bill_id,
                'room_id': room_id,
                'product_id': product_id,
                'count': count,
                'unit': pdts[product_id]['unit'],
                'money': money
            })

        return products

    def get_packs_info(self, packs, order_id, bill_id, room_id):
        if not packs:
            return packs

        pkids = [pack['pack_id'] for pack in packs]
        pks = self.ctrl.pack.get_packs_ctl(pkids)
        pks = dict((pk['id'], pk) for pk in pks)

        for pack in packs:
            count = pack['count']
            pack_id = pack['pack_id']
            price = pks[pack_id]['price']
            money = price * count
            pack.update({
                'order_id': order_id,
                'bill_id': bill_id,
                'room_id': room_id,
                'pack_id': pack_id,
                'count': count,
                'money': money,
                'md': BILL_PRO_MD['pack']
            })

        return packs

    def get_bills_product_detail(self, store_id, order_id):
        bps = self.get_order_bills_product_ctl(store_id, order_id)
        if not bps:
            return bps

        product_ids = list(set([bp['product_id'] for bp in bps if bp['product_id'] > 0]))
        pack_ids = list(set([bp['pack_id'] for bp in bps if bp['pack_id'] > 0]))

        if not product_ids:
            products_dict = {}
        else:
            products = self.ctrl.pack.get_products_ctl(product_ids)
            products_dict = dict((product['id'], product) for product in products)

        if not pack_ids:
            packs_dict = {}
        else:
            packs = self.ctrl.pack.get_packs_ctl(pack_ids)
            packs_dict = dict((pack['id'], pack) for pack in packs)

        for bp in bps:
            if bp['product_id'] > 0:
                product = products_dict[bp['product_id']]
                bp.update({
                    'name': product['name'],
                    'price': product['price']
                })
            if bp['pack_id'] > 0:
                pack = packs_dict[bp['pack_id']]
                bp.update({
                    'name': pack['name'],
                    'price': pack['price']
                })

        return bps

    def get_order_detail(self, store_id, order_no):
        '''结完帐后要打单，所以不判断订单状态'''
        order = self.get_order_ctl(store_id, order_no)
        if not order:
            raise utils.APIError(errcode=50001, errmsg='订单不存在')

        order_id = order['id']
        room_id = order['room_id']

        room = self.ctrl.room.get_room_ctl(room_id)

        if not room:
            raise utils.APIError(errcode=50001, errmsg='此包房不存在')

        order.update({
            'room_name': room['name']
        })

        bills = self.get_order_bills_ctl(store_id, order_id)
        bills = list(filter(lambda x: x['pay_state'] != BILL_PAY_STATE['cancel'], bills))

        if not bills:
            return order

        brs = self.get_order_bills_room_ctl(store_id, order_id)
        bps = self.get_bills_product_detail_ctl(store_id, order_id)

        for bill in bills:
            service_type = bill['service_type']

            if service_type == SERVICE_TYPE['prepay']:
                continue

            if service_type == SERVICE_TYPE['room']:
                blist = brs
                B_FILTER = BILL_RO_FILTER
            else:
                blist = bps
                B_FILTER = BILL_PRO_FILTER

            blist = list(filter(lambda bl: bl['bill_id'] == bill['id'], blist))

            # bill里的商品，有的有套餐(pack), pack里加上商品list
            for product in blist:
                if not product['pack_id']:
                    continue
                _, products = self.ctrl.pack.get_pack_info_ctl(store_id, product['pack_id'])
                products = [utils.dict_filter(p, PRODUCT_FILTER) for p in products]
                product.update({'list': products})

            bill.update({
                'list': [utils.dict_filter(bl, B_FILTER) for bl in blist]
            })

        order['bills'] = [utils.dict_filter(bill, BILL_FILTER) for bill in bills]

        return order

    def get_order_products(self, store_id, order_no):
        order = self.check_order_ctl(store_id, order_no)
        order_id = order['id']

        bps = self.get_bills_product_detail_ctl(store_id, order_id)

        if not bps:
            return bps

        bills = self.get_order_bills_ctl(store_id, order_id)
        bills_dict = dict((bill['id'], bill['pay_state']) for bill in bills)

        for bp in bps:
            bp.update({
                'pay_state': bills_dict[bp['bill_id']]
            })

        return bps

    def checkout_order(self, store_id, order_no, money, real_money, pay_md, describe):
        order = self.check_order_ctl(store_id, order_no)
        room_id = order['room_id']
        order_id = order['id']

        if order['pay_type'] == PAY_TYPE['current']:
            raise utils.APIError(errcode=50001, errmsg='落单后结才需要结账')

        # self.ctrl.open.update_room_ctl(store_id, room_id, ROOM_TYPE['clean'])
        self.update_order_ctl(store_id, order_no, {
            'describe': describe,
            'money': money+order.get('prepay'),
            'real_money': money+order.get('prepay'),  # real_money
            'finish_time': when.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 去掉另一个包房的订单的key
        using_order_key = self.get_using_order_key_ctl(store_id, room_id)
        self.ctrl.rs.delete(using_order_key)

        # 现金的直接支付成功
        if pay_md in (PAY_MD['cash'], PAY_MD['pos']):
            self.after_checkout_order_ctl(store_id, order_no, pay_md)

    def after_checkout_order(self, store_id, order_no, pay_md=1):
        if self.check_repeat_update_order_or_bill_ctl(store_id, order_no, 0):
            return

        self.forbid_repeat_update_order_or_bill_ctl(store_id, order_no, 0)
        orders = self.get_orders_ctl(store_id, [order_no])
        if not orders:
            return

        order = orders[0]
        order_id = order['id']
        room_id = order['room_id']
        self.ctrl.open.update_room_ctl(store_id, room_id, ROOM_TYPE['clean'])
        self.update_order_ctl(store_id, order_no, {
            'state': ORDER_STATE['finish'],
        })
        bills = self.get_order_bills_ctl(store_id, order_id)

        if not bills:
            return

        brs = self.get_order_bills_room_ctl(store_id, order_id)
        bps = self.get_order_bills_product_ctl(store_id, order_id)

        for bill in bills:
            bill_id = bill['id']
            service_type = bill['service_type']

            if service_type == SERVICE_TYPE['prepay']:
                continue

            if service_type == SERVICE_TYPE['room']:
                blist = brs
            else:
                blist = bps

            blist = list(filter(lambda bl: bl['bill_id'] == bill_id, blist))
            total_money = sum([bl['money'] for bl in blist])
            self.update_bill_ctl(store_id, bill_id, total_money, pay_md)

        # 去掉另一个包房的订单的key
        using_order_key = self.get_using_order_key_ctl(store_id, room_id)
        self.ctrl.rs.delete(using_order_key)

    def after_success_bill(self, store_id, order_no, bill_id, is_room=False):
        if self.check_repeat_update_order_or_bill_ctl(store_id, order_no, bill_id):
            return

        self.forbid_repeat_update_order_or_bill_ctl(store_id, order_no, bill_id)

        if not is_room:
            order = self.check_order_ctl(store_id, order_no)
        else:
            order = self.get_order_ctl(store_id, order_no)
        room_id = order['room_id']
        bill = self.get_bill_ctl(store_id, bill_id)
        if not bill:
            raise utils.APIError(errcode=50001, errmsg='账单不存在')

        if order['pay_type'] == PAY_TYPE['current']:
            self.dummy_update_bill_ctl(store_id, order_no, bill_id, {
                'pay_state': BILL_PAY_STATE['pay']
            })

        if bill['bill_no'].startswith('XS'):  # 续时
            minute = json.loads(bill['extra']).get('minute', 0)
            ed = utils.future_time_by_minute(order['ed'], minute, format='YYYY.MM.DD HH:mm')
            total = order['minute'] + minute
            self.update_order_money_ctl(store_id, order, bill['money'], bill['real_money'], {
                'ed': ed,
                'minute': total
            })
            self.ctrl.rs.delete(self.get_using_order_key_ctl(store_id, room_id))
        elif bill['bill_no'].startswith('KT'):  # 开台: 支付成功才锁房
            self.ctrl.open.lock_room_ctl(store_id, order['room_id'], order['describe'])
            self.update_order_ctl(store_id, order_no, {
                'state': ORDER_STATE['using'],
                'money': order['money']+bill['money'],
                'real_money': order['real_money']+bill['money']
            })
        elif bill['bill_no'].startswith('YF'):  # 预付
            self.update_order_ctl(store_id, order_no, {
                'prepay': order['prepay']+bill['money']
            })
            self.dummy_update_bill_ctl(store_id, order_no, bill_id, {
                'pay_state': BILL_PAY_STATE['pay']
            })
        elif bill['bill_no'].startswith('DD'):
            self.update_order_money_ctl(store_id, order, bill['money'], bill['real_money'])

    def close_order(self, store_id, order_no):
        order = self.check_order_ctl(store_id, order_no)
        room_id = order['room_id']

        if order['pay_type'] == PAY_TYPE['poster']:
            raise utils.APIError(errcode=50001, errmsg='落单后结要结完账才能关台')

        self.ctrl.open.update_room_ctl(store_id, room_id, ROOM_TYPE['clean'])
        self.update_order_ctl(store_id, order_no, {
            'state': ORDER_STATE['finish'],
            'finish_time': when.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        key = self.get_using_order_key_ctl(store_id, room_id)
        self.ctrl.rs.delete(key)

    def write_of_order_bills(self, store_id, order_no, bill_id):
        order = self.check_order_ctl(store_id, order_no)
        order_id = order['id']
        bill_ids = [bill_id]
        if not bill_id:
            bill_ids = self.get_order_bill_ids_ctl(store_id, order_id)
            self.update_order_ctl(store_id, order_no, dict(state=ORDER_STATE['finish']))
        for pk in bill_ids:
            self.update_bill(store_id, pk, dict(pay_state=BILL_PAY_STATE['pay']))
            self.ctrl.rs.delete(self.get_bill_key_ctl(store_id, pk))

    def cancel_bill(self, store_id, order_no, bill_id):
        bill = self.get_bill(store_id, bill_id)
        if not bill:
            raise utils.APIError(errcode=50001, errmsg='账单不存在')

        if bill['pay_state'] == BILL_PAY_STATE['finish']:
            raise utils.APIError(errcode=50001, errmsg='账单已支付,不能取消')

        self.dummy_update_bill_ctl(store_id, order_no, bill_id, {
            'pay_state': BILL_PAY_STATE['cancel']
        })

    async def pay_query(self, store_id, order_no, bill_id, paytype='wx', loop=1):
        logging.info('query order loop %s'%loop)
        key = 'query_order_%s_%s'%(order_no, bill_id)
        v = self.ctrl.rs.get(key)
        if v:
            v = eval(v)
            return v

        is_room = False
        orders = []
        if bill_id:
            orders = self.get_bills_ctl(store_id, [bill_id])
        else:
            orders = self.get_orders(store_id, [order_no])

        if not orders:
            raise utils.APIError(errcode=10001)
        order = orders[0]
        if bill_id and order['bill_no'].startswith('KT'):
            is_room = True

        url = WX_PAY_URL.format(paytype=paytype)
        pay_params = {
            'op': 'query',
            'ktvid': store_id,
            'date': str(datetime.datetime.now().date()),
            'action': 'MICROPAY',
            'data': json.dumps({
                'paraOutTradeNo': order['pay_id']
            }),
            'erp_id': order_no,
            'time': int(datetime.datetime.now().timestamp())
        }
        try:
            http_client = utils.get_async_client()
            request = utils.http_request(url_concat(url, pay_params), method='POST', body='')

            res = await utils.fetch(http_client, request)
            res = json.loads(res.body.decode())
            logging.info('query order order_no: %s, bill_id: %s result: %s'%(order_no, bill_id, res))
            if utils.is_success_pay(paytype, res):
                pl = self.ctrl.rs.pipeline(transaction=True)
                pl.set(key, res).expire(key, 15*60).execute()
                self.success_pay_ctl(store_id, order_no, bill_id, paytype, is_room)
            elif loop > 0:
                IOLoop.current().add_timeout(time.time()+10, self.pay_query_ctl, store_id, order_no, bill_id, paytype, loop-1)
            return res
        except Exception as e:
            logging.error(e)
            if loop > 0:
                IOLoop.current().add_timeout(time.time()+10, self.pay_query_ctl, store_id, order_no, bill_id, paytype, loop-1)
            return {}

    def success_pay(self, store_id, order_no, bill_id, paytype, is_room=False):
        if bill_id:
            self.after_success_bill_ctl(store_id, order_no, bill_id, is_room=is_room)
            return
        pay_md = 2 if paytype=='wx' else 3
        self.after_checkout_order_ctl(store_id, order_no, pay_md)

    async def post_pay(self, store_id, order_no, bill_id, auth_code, paytype):
        key = 'query_order_%s_%s'%(order_no, bill_id)
        self.ctrl.rs.delete(key)
        if bill_id:
            orders = self.get_bills_ctl(store_id, [bill_id])
        else:
            orders = self.get_orders(store_id, [order_no])

        if not orders:
            raise utils.APIError(errcode=10001)
        order = orders[0]
        total_fee = order['money']

        url = WX_PAY_URL.format(paytype=paytype)
        pay_params = {
            'op': 'fastpay',
            'ktvid': store_id,
            'date': str(datetime.datetime.now().date()),
            'action': 'MICROPAY',
            'data': json.dumps({
                'ktv_id': store_id,
                'erp_id': order_no,
                'paraTotalFee': total_fee if not options.debug else 1,
                'paraAuthCode': auth_code,
                'paraBody': 'body',
                'paraBillCreateIp': '',
            }),
            'erp_id': order_no,
            'time': int(datetime.datetime.now().timestamp())
        }
        try:
            http_client = utils.get_async_client()
            request = utils.http_request(url_concat(url, pay_params), method='POST', body='')

            res = await utils.fetch(http_client, request)
            res = json.loads(res.body.decode())
            logging.info('query order result: %s'%res)
            return res
        except Exception as e:
            logging.error(e)
            return {}
