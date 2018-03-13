#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from lib import utils


class CalcCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl

    def by_time(self, store_id, phone, rt_id, room_id, st, ed):
        store = self.ctrl.store.get_store_ctl(phone)
        store_st = store['st']
        store_ed = store['ed']

        # 兼容续时跨天
        day = datetime.datetime.now().date()
        order = self.ctrl.order.get_using_order_ctl(store_id, room_id)
        if order:
            order_ed = order['ed']
            day = datetime.datetime.strptime(order_ed[:-6], '%Y.%m.%d')
            if order_ed[-5:] < store_st:
                day = day - datetime.timedelta(days=1)
            day = day.date()

        holiday_fees = self.ctrl.room.get_holiday_room_fees_ctl(store_id, rt_id, day=day)

        if holiday_fees:
            fees = holiday_fees
        else:
            fees = self.ctrl.room.get_week_room_fees_ctl(store_id, rt_id, day=day)

        sorted_fees = sorted(fees, key=lambda f: f['st'])

        if not utils.is_valid_fees(sorted_fees, store_st, store_ed):
            raise utils.APIError(errcode=50001, errmsg='计费方式设置和营业时间不匹配')

        bills = utils.get_time_bills(sorted_fees, st, ed)

        return bills

    def by_pack(self, store_id, rt_id, st, pack_id):
        pack = self.ctrl.pack.get_pack_ctl(pack_id)

        if not pack:
            raise utils.APIError(errcode=50001, errmsg='该套餐不存在')

        if not utils.is_valid_pack(pack):
            raise utils.APIError(errcode=50001, errmsg='该套餐已下架')

        pack_st = pack['st']
        pack_ed = pack['ed']
        price = pack['price']
        hour = pack['hour']
        name = pack['name']
        pack_id = pack['id']

        if not utils.is_hour_in_range(st[-5:], pack_st, pack_ed):
            raise utils.APIError(errcode=50001, errmsg='开台时间需在套餐的有效时间之内')

        minute = hour * 60
        if len(st) > 6:
            ed = utils.future_time_by_hour(st, hour, 'YYYY.MM.DD HH:mm')
        else:
            ed = utils.future_time_by_hour(st, hour)


        bill = {
            'pack_id': pack_id,
            'name': name,
            'st': st,
            'ed': ed,
            'minute': minute,
            'price': price
        }

        return bill
