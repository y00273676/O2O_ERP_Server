#!/usr/bin/env python
# -*- coding: utf-8 -*-

import when
import pickle
import pdb

from lib import utils
from settings import A_DAY, STATE


class RoomCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.room = ctrl.pdb.room

    def __getattr__(self, name):
        return getattr(self.room, name)

    def get_room_types_key(self, store_id):
        return 't_room_types_%s' % store_id

    def get_room_key(self, room_id):
        return 't_room_%s' % room_id

    def get_rt_room_ids_key(self, store_id, rt_id):
        return 't_rt_room_ids_%s_%s' % (store_id, rt_id)

    def get_store_room_ids_key(self, store_id):
        return 't_store_room_ids_%s' % store_id

    def get_room_fees_key(self, store_id, rt_id, md, day_or_holiday):
        return 't_room_fees_%s_%s_%s_%s' % (store_id, rt_id, md, day_or_holiday)

    def get_room_pack_ids_key(self, store_id, rt_id):
        return 't_room_pack_ids_%s_%s' % (store_id, rt_id)

    def add_room_types(self, store_id, names):
        room_types = self.room.add_room_types(store_id, names)
        key = self.get_room_types_key_ctl(store_id)
        self.ctrl.rs.delete(key)
        return room_types

    def get_room_types(self, store_id):
        key = self.get_room_types_key_ctl(store_id)
        room_type = self.ctrl.rs.get(key)

        if room_type:
            return pickle.loads(room_type)

        room_type = self.room.get_room_types(store_id)
        if room_type:
            self.ctrl.rs.set(key, pickle.dumps(room_type),  7 * A_DAY)

        return room_type

    def get_room_type(self, store_id, rt_id):
        room_types = self.get_room_types_ctl(store_id)
        for rt in room_types:
            if rt['id'] == rt_id:
                return rt
        return {}

    def delete_room_type(self, store_id, rt_id):
        self.room.delete_room_type(store_id, rt_id)
        room_ids = self.get_rt_room_ids_ctl(store_id, rt_id)
        for room_id in room_ids:
            self.delete_room_ctl(room_id, store_id)
        key = self.get_room_types_key_ctl(store_id)
        self.ctrl.rs.delete(key)

    def update_room_type(self, store_id, rt_id, data):
        self.room.update_room_type(rt_id, store_id, data=data)
        key = self.get_room_types_key_ctl(store_id)
        self.ctrl.rs.delete(key)

    def check_room_exists(self, store_id, rooms, room_id=0):
        store_rooms = self.get_store_rooms_ctl(store_id)
        if room_id:
            store_rooms = list(filter(lambda x: x.get('id')!=room_id, store_rooms))

        al_names = list(set([r['name'] for r in store_rooms]).intersection(set([r['name'] for r in rooms])))
        al_macs = list(set(r['name'] for r in store_rooms).intersection(set([r['mac'] for r in rooms])))
        if al_macs or al_names:
            msg = ('地址'+'和'.join(al_macs)) if al_macs else ('房间名'+'和'.join(al_names))
            msg += '已存在'
            raise utils.APIError(errcode=50001, errmsg=msg)

    def add_rooms(self, store_id, rooms):
        room_list = []
        [room_list.extend(_rooms) for _rooms in rooms.values()]
        self.check_room_exists_ctl(store_id, room_list)

        room_list = self.room.add_rooms(store_id, rooms)
        for rt_id in rooms.keys():
            r_key = self.get_rt_room_ids_key_ctl(store_id, rt_id)
            s_key = self.get_store_room_ids_key_ctl(store_id)
            self.ctrl.rs.delete(r_key, s_key)
        return room_list

    def get_rooms(self, room_ids=[]):
        if not room_ids:
            return []

        multi_key = [self.get_room_key_ctl(room_id) for room_id in room_ids]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_room = dict(zip(multi_key, cached))
        miss_ids = [room_id for room_id in room_ids if multi_room[self.get_room_key_ctl(room_id)] is None]
        if not miss_ids:
            return [multi_room[self.get_room_key_ctl(room_id)] for room_id in room_ids]

        miss_room_list = self.room.get_rooms(tuple(miss_ids))
        miss_ids = [miss_room['id'] for miss_room in miss_room_list]
        miss_multi_key = [self.get_room_key_ctl(room_id) for room_id in miss_ids]
        miss_room = dict(zip(miss_multi_key, miss_room_list))

        if miss_room:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_room_encode = dict((key, pickle.dumps(miss_room[key])) for key in miss_room)
            pl.mset(miss_room_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_room.update(miss_room)
        return [multi_room[self.get_room_key_ctl(room_id)] for room_id in room_ids if self.get_room_key_ctl(room_id) in multi_room]

    def get_rt_room_ids(self, store_id, rt_id):
        key = self.get_rt_room_ids_key_ctl(store_id, rt_id)
        room_ids = self.ctrl.rs.lrange(key, 0, -1)

        if room_ids:
            return [int(room_id) for room_id in room_ids]

        room_ids = self.room.get_rt_room_ids(store_id, rt_id)
        if not room_ids:
            return room_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *room_ids).expire(key, A_DAY).execute()
        return room_ids

    def get_store_room_ids(self, store_id):
        key = self.get_store_room_ids_key_ctl(store_id)
        room_ids = self.ctrl.rs.lrange(key, 0, -1)

        if room_ids:
            return [int(room_id) for room_id in room_ids]

        room_ids = self.room.get_store_room_ids(store_id)
        if not room_ids:
            return room_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *room_ids).expire(key, A_DAY).execute()
        return room_ids

    def get_rt_rooms(self, store_id, rt_id):
        room_ids = self.get_rt_room_ids_ctl(store_id, rt_id)
        if not room_ids:
            return []
        rooms = self.get_rooms_ctl(room_ids)
        return rooms

    def get_room(self, room_id):
        rooms = self.get_rooms_ctl([room_id])
        if not rooms:
            return {}
        return rooms[0]

    def delete_room(self, room_id, store_id):
        room = self.room.delete_room(room_id, store_id)
        if room:
            key = self.get_room_key_ctl(room_id)
            r_key = self.get_rt_room_ids_key_ctl(store_id, room['rt_id'])
            s_key = self.get_store_room_ids_key_ctl(store_id)
            self.ctrl.rs.delete(key, r_key, s_key)

    def update_room(self, room_id, store_id, data, check=False):
        if check:
            self.check_room_exists_ctl(store_id, [data], room_id)

        room = self.room.update_room(room_id, store_id, data=data)
        if room:
            key = self.get_room_key_ctl(room_id)
            r_key = self.get_rt_room_ids_key_ctl(store_id, room['rt_id'])
            s_key = self.get_store_room_ids_key_ctl(store_id)
            self.ctrl.rs.delete(key, r_key, s_key)

    def get_store_rooms(self, store_id):
        room_ids = self.get_store_room_ids_ctl(store_id)
        if not room_ids:
            return []
        rooms = self.get_rooms_ctl(room_ids)
        room_types = self.get_room_types_ctl(store_id)
        rtid_name_dict = {r['id']: r['name'] for r in room_types}
        [r.update({'rt_name': rtid_name_dict[r['rt_id']]}) for r in rooms]
        return rooms

    def _remove_all_room_fee_key(self, store_id, rt_id, md, day_or_holiday):
        key = self.get_room_fees_key_ctl(store_id, rt_id, md, day_or_holiday)
        all_key = self.get_room_fees_key_ctl(store_id, rt_id, md, '*')
        all_keys = self.ctrl.rs.keys(all_key)
        all_keys.append(key)
        self.ctrl.rs.delete(*all_keys)

    def add_room_fees(self, store_id, rt_id, fees):
        fee_list = self.room.add_room_fees(store_id, rt_id, fees)
        for fee in fees:
            day = fee.get('day', '')
            holiday = fee.get('holiday', '')
            day_or_holiday = day or holiday
            self._remove_all_room_fee_key_ctl(store_id, rt_id, 'day' if day else 'holiday', day_or_holiday)
        return fee_list

    def get_room_fees(self, store_id, rt_id, day_or_holiday, md):
        key = self.get_room_fees_key_ctl(store_id, rt_id, md, day_or_holiday)
        room_fees = self.ctrl.rs.get(key)

        if room_fees:
            return pickle.loads(room_fees)

        room_fees = self.room.get_room_fees(store_id, rt_id, day_or_holiday, md)
        if room_fees:
            self.ctrl.rs.set(key, pickle.dumps(room_fees),  7 * A_DAY)

        return room_fees

    def get_holiday_room_fees(self, store_id, rt_id, day=None):
        day = day if day else when.today()
        fees = self.get_room_fees_ctl(store_id, rt_id, str(day), 'holiday')
        return fees

    def get_week_room_fees(self, store_id, rt_id, day=None):
        week_of_day = utils.get_day_of_week(day)
        fees = self.get_room_fees_ctl(store_id, rt_id, str(week_of_day), 'day')
        return fees

    def delete_room_fees(self, store_id, rt_id, day_or_holiday, md):
        self.room.delete_room_fees(store_id, rt_id, day_or_holiday, md)
        self._remove_all_room_fee_key_ctl(store_id, rt_id, md, day_or_holiday)

    def delete_room_fee(self, store_id, fee_id):
        fee = self.room.delete_room_fee(store_id, fee_id)
        if fee:
            md = fee['md']
            day_or_holiday = fee['day_or_holiday']
            self._remove_all_room_fee_key_ctl(store_id, fee['rt_id'], md, day_or_holiday)

    def update_room_fee(self, fee_id, store_id, data):
        fee = self.room.update_room_fee(fee_id, store_id, data=data)
        if fee:
            md = fee['md']
            day_or_holiday = fee['day_or_holiday']
            self._remove_all_room_fee_key_ctl(store_id, fee['rt_id'], md, day_or_holiday)

    def get_room_pack_ids(self, store_id, rt_id):
        key = self.get_room_pack_ids_key_ctl(store_id, rt_id)
        pack_ids = self.ctrl.rs.lrange(key, 0, -1)

        if pack_ids:
            return [int(pid) for pid in pack_ids]

        pack_ids = self.room.get_room_pack_ids(store_id, rt_id)
        if not pack_ids:
            return pack_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *pack_ids).expire(key, A_DAY).execute()
        return pack_ids

    def get_room_packs(self, store_id, rt_id):
        pack_ids = self.get_room_pack_ids_ctl(store_id, rt_id)
        if not pack_ids:
            return []
        packs = self.ctrl.pack.get_packs_ctl(pack_ids)
        return packs

    def add_room_pack(self, store_id, rt_id, products, data):
        '''
        添加包房套餐：
        1、创建套餐t_pack
        2、创建包房和套餐的关系t_room_pack
        3、创建套餐和酒水的关系t_pack_product
        '''
        data.update({
            'store_id': store_id
        })

        pack = self.ctrl.pack.add_pack(data)
        pack_id = pack['id']
        self.room.add_room_pack(store_id, rt_id, pack_id)

        key = self.get_room_pack_ids_key_ctl(store_id, rt_id)
        self.ctrl.rs.delete(key)

        pts_dict = dict((int(p['product_id']), p) for p in products)
        product_ids = pts_dict.keys()

        if not product_ids:
            return pack

        products = self.ctrl.pack.get_products_ctl(product_ids)
        valid_products = [pts_dict[product['id']] for product in products]

        if valid_products:
            self.ctrl.pack.add_pack_products(store_id, pack_id, valid_products)
            key = self.ctrl.pack.get_pack_products_key_ctl(store_id, pack_id)
            self.ctrl.rs.delete(key)

        return pack

    def delete_room_pack(self, store_id, rt_id, pack_id):
        self.room.delete_room_pack(store_id, pack_id)
        self.ctrl.pack.delete_pack(store_id, pack_id)
        pack_key = self.ctrl.pack.get_pack_key_ctl(pack_id)
        rpack_ids_key = self.get_room_pack_ids_key_ctl(store_id, rt_id)
        self.ctrl.rs.delete(pack_key, rpack_ids_key)

