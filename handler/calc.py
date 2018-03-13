#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler


class ByTimeHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        计时时段房费计算
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            st = args['st']
            ed = args['ed']

            assert(utils.is_valid_time(st))
            assert(utils.is_valid_time(ed))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        phone = self.current_user['phone']
        store_id = self.current_user['store_id']

        data = {
            'name': '计时',
            'list': []
        }

        room = ctrl.room.get_room_ctl(room_id)
        rt = ctrl.room.get_room_type_ctl(store_id, rt_id)
        data.update({
            'rt_name': rt.get('name', ''),
            'room_name': room.get('name', '')
        })
        data['list'] = ctrl.calc.by_time_ctl(store_id, phone, rt_id, room_id, st, ed)

        self.send_json(data)


class ByPackHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        套餐房费计算
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            st = args['st']
            pack_id = int(args['pack_id'])

            assert(utils.is_valid_time(st))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'detail': {}
        }

        data['detail'] = ctrl.calc.by_pack_ctl(self.current_user['store_id'], rt_id, st, pack_id)

        self.send_json(data)

