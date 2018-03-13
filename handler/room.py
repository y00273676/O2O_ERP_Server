#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler
from settings import ROOM_TYPE, PAY_TYPE, ORDER_STATE


class TypeHandler(BaseHandler):

    @erp_auth
    def post(self):
        '''
        添加包房类型
        '''
        try:
            args = json.loads(self.request.body.decode())
            names = args['names']
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'list': []
        }

        if not names:
            return self.send_json(data)

        room_types = ctrl.room.add_room_types_ctl(self.current_user['store_id'], names)

        if not room_types:
            return self.send_json(data)

        FILTER = (
            {'id': 'rt_id'},
            'store_id',
            'name',
            'update_time'
        )
        data['list'] = [utils.dict_filter(room_type, FILTER) for room_type in room_types]

        self.send_json(data)

    @erp_auth
    def get(self):
        '''
        获取所有的包房类型
        '''
        data = {
            'list': []
        }

        room_types = ctrl.room.get_room_types_ctl(self.current_user['store_id'])

        if not room_types:
            return self.send_json(data)

        FILTER = (
            {'id': 'rt_id'},
            'store_id',
            'name',
            'pic',
            'min_man',
            'max_man',
            'update_time'
        )
        data['list'] = [utils.dict_filter(room_type, FILTER) for room_type in room_types]

        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        删除某个包房类型
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.room.delete_room_type_ctl(self.current_user['store_id'], rt_id)

        self.send_json()

    @erp_auth
    def put(self):
        '''
        修改某个包房类型
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            name = args.get('name', '')
            pic = args.get('pic', '')
            min_man = int(args.get('min_man', 0))
            max_man = int(args.get('max_man', 0))

            assert(name or pic or min_man or max_man)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'name': name,
            'pic': pic
        }

        if 'min_man' in args:
            data.update({
                'min_man': min_man
            })

        if 'max_man' in args:
            data.update({
                'max_man': max_man
            })

        ctrl.room.update_room_type_ctl(self.current_user['store_id'], rt_id, data)

        self.send_json()


class IPHandler(BaseHandler):

    def get_rt_rooms(self, store_id, rt_id):
        rooms = ctrl.room.get_rt_rooms_ctl(store_id, rt_id)

        if not rooms:
            return rooms

        FILTER = (
            {'id': 'room_id'},
            'store_id',
            'rt_id',
            'name',
            'ip',
            'mac',
            'update_time'
        )
        rooms = [utils.dict_filter(room, FILTER) for room in rooms]
        return rooms

    def get_store_rooms(self):
        store_id = self.current_user['store_id']
        rooms = ctrl.room.get_store_rooms_ctl(store_id)

        if not rooms:
            return rooms

        using_states = (ROOM_TYPE['using'], ROOM_TYPE['timeout'])
        using_rooms = [room for room in rooms if room['room_type'] in using_states]
        FILTER = (
            {'id': 'room_id'},
            'store_id',
            'rt_id',
            'rt_name',
            'name',
            'mac',
            'room_type',
            'st',
            'ed',
            'minute',
            'order_no',
            'prepay',
            'pay_md',
            'state',
            'pay_type',
            'describe',
            'pay_state'
        )

        if not using_rooms:
            rooms = [utils.dict_filter(room, FILTER) for room in rooms]
            return rooms

        room_ids = [room['id'] for room in using_rooms]
        orders = ctrl.order.get_using_orders_ctl(store_id, room_ids)
        # 开台后 有 没有订单的情况
        orders = list(filter(bool, orders))
        orders_dict = dict((order['room_id'], order) for order in orders)

        for room in rooms:
            if room['room_type'] in using_states and room['id'] in orders_dict:
                order = orders_dict[room['id']]
                order.pop('id')
                order.update({'pay_state': order['state']})
                order.pop('state')
                room.update(order)

        rooms = [utils.dict_filter(room, FILTER) for room in rooms]
        return rooms

    @erp_auth
    def get(self):
        '''
        获取包房列表
        '''
        try:
            rt_id = int(self.get_argument('rt_id', 0))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'list': []
        }

        if rt_id:
            data['list'] = self.get_rt_rooms(self.current_user['store_id'], rt_id)
            return self.send_json(data)

        data['list'] = self.get_store_rooms()
        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        往某个包房类型下添加包房
        '''
        try:
            args = json.loads(self.request.body.decode())
            rooms = {}
            for arg in args:
                rt_id = arg['rt_id']
                rooms[rt_id] = []
                for ip_name in arg['list']:
                    assert(ip_name['name'])
                    rooms[rt_id].append(ip_name)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'list': []
        }

        rooms = ctrl.room.add_rooms_ctl(self.current_user['store_id'], rooms)

        if not rooms:
            return self.send_json(data)

        FILTER = (
            {'id': 'room_id'},
            'store_id',
            'rt_id',
            'name',
            'mac',
            'ip',
            'room_type',
            'describe',
            'update_time'
        )
        data['list'] = [utils.dict_filter(room, FILTER) for room in rooms]

        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        删除某个包房
        '''
        try:
            room_id = int(self.get_argument('room_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.room.delete_room_ctl(room_id, self.current_user['store_id'])

        self.send_json()

    @erp_auth
    def put(self):
        '''
        修改某个包房
        '''
        try:
            args = json.loads(self.request.body.decode())
            rt_id = int(args['rt_id'])
            room_id = int(args['room_id'])
            name = args.get('name', '')
            ip = args.get('ip', '')
            mac = args.get('mac', '')
            room_type = int(args.get('room_type', 0))

            assert(utils.is_ip_address(ip))
            assert(rt_id > 0)
            if 'room_type' in args:
                assert(room_type in ROOM_TYPE.values())
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']

        room = ctrl.room.get_room_ctl(room_id)

        if not room:
            raise utils.APIError(errcode=50001, errmsg='包房无效')

        data = {
            'name': name,
            'ip': ip,
            'mac': mac
        }

        if 'room_type' not in args:
            ctrl.room.update_room_ctl(room_id, store_id, data, check=True)
            return self.send_json()

        # order = ctrl.order.get_using_order_ctl(store_id, room_id)
        order = ctrl.order.get_using_orders(store_id, [room_id])
        if order and order[0].get('state', 0)==ORDER_STATE['using']:
            errmsg = '请先关台' if order[0]['pay_type'] == PAY_TYPE['current'] else '请先结账'
            raise utils.APIError(errcode=50001, errmsg=errmsg)

        data.update({
            'room_type': room_type
        })
        ctrl.room.update_room_ctl(room_id, store_id, data, check=True)

        self.send_json()


class FeeHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取某房型下周几/假期内的所有计费设置
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
            md = self.get_argument('md', 'day')
            day_or_holiday = self.get_argument('day_or_holiday', '')
            assert(md in ('day', 'holiday'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'list': []
        }

        room_fees = ctrl.room.get_room_fees_ctl(self.current_user['store_id'], rt_id, day_or_holiday, md)

        if not room_fees:
            return self.send_json(data)

        FILTER = (
            {'id': 'fee_id'},
            'store_id',
            'rt_id',
            'st',
            'ed',
            'fee',
            'day_or_holiday',
            'update_time'
        )

        room_fees = [utils.dict_filter(fee, FILTER) for fee in room_fees]
        data['list'] = room_fees

        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        添加计费设置
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
            args = json.loads(self.request.body.decode())
            for arg in args:
                assert(arg.get('day') or arg.get('holiday'))
                for item in arg['list']:
                    assert(utils.is_valid_time(item['st']))
                    assert(utils.is_valid_time(item['ed']))
                    assert(int(item['fee']) > 0)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        room_fees = ctrl.room.add_room_fees_ctl(self.current_user['store_id'], rt_id, args)

        data = {
            'list': []
        }

        if not room_fees:
            return self.send_json(data)

        FILTER = (
            {'id': 'fee_id'},
            'store_id',
            'rt_id',
            'st',
            'ed',
            'fee',
            'day_or_holiday',
            'update_time'
        )

        data['list'] = [utils.dict_filter(fee, FILTER) for fee in room_fees]

        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        删除计费设置
        '''
        has_fee_id = self.has_argument('fee_id')

        if has_fee_id:
            self._del_fee()
        else:
            self._del_fees()

    def _del_fee(self):
        '''
        删除某条计费规则
        '''
        try:
            fee_id = int(self.get_argument('fee_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.room.delete_room_fee_ctl(self.current_user['store_id'], fee_id)

        self.send_json()

    def _del_fees(self):
        '''
        清空计费规则
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
            md = self.get_argument('md', 'day')
            day_or_holiday = self.get_argument('day_or_holiday', '')
            assert(md in ('day', 'holiday'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.room.delete_room_fees_ctl(self.current_user['store_id'], rt_id, day_or_holiday, md)

        self.send_json()

    @erp_auth
    def put(self):
        '''
        修改某条计费设置
        '''
        try:
            args = json.loads(self.request.body.decode())
            fee_id = int(args['fee_id'])
            st = args.get('st', '')
            ed = args.get('ed', '')
            fee = int(args.get('fee', 0))

            assert(utils.is_valid_time(st))
            assert(utils.is_valid_time(ed))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'st': st,
            'ed': ed
        }

        if 'fee' in args:
            data.update({
                'fee': fee
            })

        ctrl.room.update_room_fee_ctl(fee_id, self.current_user['store_id'], data)

        self.send_json()


class PackHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取某房型下的所有的酒水套餐
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
            is_valid = int(self.get_argument('is_valid', 0))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'list': []
        }
        FILTER = (
            {'id': 'pack_id'},
            'store_id',
            'name',
            'start_date',
            'end_date',
            'st',
            'ed',
            'price',
            'day',
            'hour',
            'state',
            'update_time'
        )

        packs = ctrl.room.get_room_packs_ctl(self.current_user['store_id'], rt_id)

        if not packs:
            return self.send_json(data)

        if is_valid:
            _packs = [pack for pack in packs if utils.is_valid_pack(pack)]
            packs = _packs

        packs = [utils.dict_filter(pack, FILTER) for pack in packs]

        data['list'] = packs

        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        给某房型添加酒水套餐
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
            args = json.loads(self.request.body.decode())
            name = args['name']
            start_date = args['start_date']
            end_date = args['end_date']
            price = int(args['price'])
            day = args['day']
            st = args['st']
            ed = args['ed']
            hour = int(args['hour'])
            products = args.get('list', [])

            assert(utils.is_valid_day_value(day))
            assert(utils.is_valid_time(st))
            assert(utils.is_valid_time(ed))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        pack = ctrl.room.add_room_pack_ctl(self.current_user['store_id'], rt_id, products, {
            'name': name,
            'start_date': start_date,
            'end_date': end_date,
            'price': price,
            'day': day,
            'st': st,
            'ed': ed,
            'hour': hour,
            'md': 'room'
        })

        data = {
            'detail': {}
        }
        FILTER = (
            {'id': 'pack_id'},
            'store_id',
            'name',
            'start_date',
            'end_date',
            'st',
            'ed',
            'price',
            'day',
            'hour',
            'state',
            'update_time'
        )
        data['detail'] = utils.dict_filter(pack, FILTER)

        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        删除某房型酒水套餐
        '''
        try:
            rt_id = int(self.get_argument('rt_id'))
            pack_id = int(self.get_argument('pack_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.room.delete_room_pack_ctl(self.current_user['store_id'], rt_id, pack_id)

        self.send_json()

    @erp_auth
    def put(self):
        '''
        修改某房型下的酒水套餐
        '''
        try:
            args = json.loads(self.request.body.decode())
            pack_id = int(args['pack_id'])
            name = args.get('name', '')
            start_date = args.get('start_date', '')
            end_date = args.get('end_date', '')
            day = args.get('day', '')
            st = args.get('st', '')
            ed = args.get('ed', '')
            price = int(args.get('price', 0))
            hour = int(args.get('hour', 0))
            state = int(args.get('state', 0))

            assert(utils.is_valid_date(start_date))
            assert(utils.is_valid_date(end_date))
            assert(utils.is_valid_day_value(day))
            assert(utils.is_valid_time(st))
            assert(utils.is_valid_time(ed))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'name': name,
            'start_date': start_date,
            'end_date': end_date,
            'day': day,
            'st': st,
            'ed': ed,
            'md': 'room'
        }

        if 'state' in args:
            data.update({
                'state': state
            })

        if 'price' in args:
            data.update({
                'price': price
            })

        if 'hour' in args:
            data.update({
                'hour': hour
            })

        ctrl.pack.update_pack_ctl(self.current_user['store_id'], pack_id, data)

        self.send_json()
