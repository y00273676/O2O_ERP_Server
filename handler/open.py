#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler
from settings import PAY_MD, PAY_TYPE


class ByTimeHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        计时时段开台
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            st = args['st']
            ed = args['ed']
            pay_type = int(args['pay_type'])
            describe = args['describe']
            pay_md = int(args.get('pay_md', 1))
            rate = int(args.get('rate', 100))
            money = int(args.get('money', 0))
            real_money = int(args.get('real_money', 0))

            pay_data = {
                'pay_type': pay_type,
                'describe': describe,
                'pay_md': pay_md,
                'rate': rate,
                'money': money,
                'real_money': real_money
            }

            assert(pay_type in PAY_TYPE.values())
            assert(pay_md in PAY_MD.values())
            assert(rate == 100)
            # assert(utils.is_valid_time(st) and utils.is_valid_time(ed))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']
        phone = self.current_user['phone']

        data = {
            'detail': {}
        }

        data['detail'] = ctrl.open.by_time_ctl(store_id, phone, rt_id, room_id, st, ed, pay_data)

        self.send_json(data)


class ByPackHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        套餐房费开台
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            st = args['st']
            pack_id = int(args['pack_id'])
            pay_type = int(args['pay_type'])
            describe = args['describe']
            pay_md = int(args.get('pay_md', 1))
            rate = int(args.get('rate', 100))
            money = int(args.get('money', 0))
            real_money = int(args.get('real_money', 0))

            pay_data = {
                'pay_type': pay_type,
                'describe': describe,
                'pay_md': pay_md,
                'rate': rate,
                'money': money,
                'real_money': real_money
            }

            # assert(utils.is_valid_time(st))
            assert(pay_type in PAY_TYPE.values())
            assert(pay_md in PAY_MD.values())
            assert(rate == 100)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'detail': {}
        }

        store_id = self.current_user['store_id']

        data['detail'] = ctrl.open.by_pack_ctl(store_id, rt_id, room_id, st, pack_id, pay_data)

        self.send_json(data)

