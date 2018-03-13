#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import exc

from lib import utils
from settings import ROOM_TYPE, PAY_TYPE, PAY_MD


class OpenCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def check_room_valid(self, store_id, rt_id, room_id):
        room = self.ctrl.room.get_room_ctl(room_id)

        if not room:
            raise utils.APIError(errcode=50001, errmsg='包房不存在')

        if room['room_type'] not in [ROOM_TYPE['free']]:
            raise utils.APIError(errcode=50001, errmsg='包房被占用')

        return room

    def lock_room(self, store_id, room_id, describe):
        self.update_room_ctl(store_id, room_id, ROOM_TYPE['using'], describe)

    def unlock_room(self, store_id, room_id):
        order = self.ctrl.order.get_using_order_ctl(store_id, room_id)
        if order:
            self.ctrl.order.disable_order_ctl(store_id, order['order_no'], room_id)
        self.update_room_ctl(store_id, room_id, ROOM_TYPE['free'])

    def update_room(self, store_id, room_id, room_type, describe=''):
        self.ctrl.room.update_room_ctl(room_id, store_id, {
            'room_type': room_type,
            'describe': describe
        })

    def by_time(self, store_id, phone, rt_id, room_id, st, ed, pay_data):
        '''
        计时开台操作步骤：
        1、先锁房
        2、创建订单
        3、创建流水单
        4、创建计时流水明细
        '''
        describe = pay_data['describe']
        pay_md = pay_data['pay_md']
        pay_type = pay_data['pay_type']
        money = pay_data['money']
        real_money = pay_data['real_money']
        rate = pay_data['rate']

        self.check_room_valid_ctl(store_id, rt_id, room_id)
        fee_bills = self.ctrl.calc.by_time_ctl(store_id, phone, rt_id, room_id, st, ed)

        try:
            order = self.ctrl.order.add_order_ctl(store_id, room_id, st, ed, money, real_money, pay_type, describe)
            bill = self.ctrl.order.add_bill_ctl(store_id, room_id, pay_type, order['id'], money, real_money, rate, pay_md, order_no=order['order_no'])
            self.ctrl.order.add_bill_room_ctl(store_id, phone, rt_id, room_id, st, ed, order['id'], bill['id'], fee_bills)

            if utils.check_if_success_bill(pay_type, pay_md):
                self.lock_room_ctl(store_id, room_id, describe)
                self.ctrl.order.after_success_bill_ctl(store_id, order['order_no'], bill['id'], is_room=True)

            return {
                'order_no': order['order_no'],
                'bill_no': bill['bill_no'],
                'bill_id': bill['id']
            }
        except exc.SQLAlchemyError as e:
            logging.error(str(e))
            self.unlock_room_ctl(store_id, room_id)
            raise

    def by_pack(self, store_id, rt_id, room_id, st, pack_id, pay_data):
        '''
        套餐开台操作步骤：
        1、先锁房
        2、创建订单
        3、创建流水单
        4、创建套餐流水明细
        '''
        describe = pay_data['describe']
        pay_md = pay_data['pay_md']
        pay_type = pay_data['pay_type']
        money = pay_data['money']
        real_money = pay_data['real_money']
        rate = pay_data['rate']

        self.check_room_valid_ctl(store_id, rt_id, room_id)
        by_pack = self.ctrl.calc.by_pack_ctl(store_id, rt_id, st, pack_id)
        ed = by_pack['ed']
        minute = by_pack['minute']

        try:
            order = self.ctrl.order.add_order_ctl(store_id, room_id, st, ed, money, real_money, pay_type, describe)
            bill = self.ctrl.order.add_bill_ctl(store_id, room_id, pay_type, order['id'], money, real_money, rate, pay_md, order_no=order['order_no'])
            self.ctrl.order.add_bill_room_by_pack_ctl(store_id, order['id'], bill['id'], room_id, pack_id, st, ed, minute, money)

            if utils.check_if_success_bill(pay_type, pay_md):
                self.lock_room_ctl(store_id, room_id, describe)
                self.ctrl.order.after_success_bill_ctl(store_id, order['order_no'], bill['id'], is_room=True)

            return {
                'order_no': order['order_no'],
                'bill_no': bill['bill_no'],
                'bill_id': bill['id']
            }
        except exc.SQLAlchemyError as e:
            logging.error(str(e))
            self.unlock_room_ctl(store_id, room_id)
            raise

