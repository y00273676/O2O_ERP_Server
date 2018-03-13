import unittest
import json
import time
import subprocess
import pdb

from control import ctrl
from mysql import pdb as db

from pprint import pprint
from tests import AsyncHTTPTestCase, current_time_str


class RoomTest(AsyncHTTPTestCase):

    def _remove_redis_keys(self, keys):
        for k in keys:
            ks = ctrl.rs.keys(k)
            ks = [i.decode() for i in ks]
            [ctrl.rs.delete(key) for key in keys]

    def _clear_room_data_of_store_id(self, store_id):
        db.room.slave.execute('delete from t_room_type where store_id=%s'%store_id)
        db.room.slave.execute('delete from t_room where store_id=%s'%store_id)
        db.room.slave.execute('delete from t_room_fee where store_id=%s'%store_id)
        db.room.slave.execute('delete from t_room_pack where store_id=%s'%store_id)
        db.room.slave.commit()

        types_key = ctrl.room.get_room_types_key_ctl(store_id)
        rooms_key = ctrl.room.get_rooms_key_ctl(store_id, '*')
        packs_key = ctrl.room.get_room_pack_ids_key_ctl(store_id, '*')
        fees_key = ctrl.room.get_room_fees_key_ctl(store_id, '*', '*', '*')

        self._remove_redis_keys([types_key, rooms_key, packs_key, fees_key])

    def setUp(self):
        super(RoomTest, self).setUp()
        self.user = dict(store_id=10000113, phone='15990187931')
        self.token = self.gen_token(self.user['phone'], self.user['store_id'])
        self.url = '/room/type'
        self._clear_room_data_of_store_id(self.user['store_id'])

    def test_type(self):
        # fetch room types, get list: []
        res = self.get(self.url, params=dict(token=self.token))
        res = json.loads(res.body.decode())
        self.assertEqual(200, second=res['errcode'])
        self.assertEqual(len(res['list']), 0)

        # post room type:
        time.sleep(2)
        names = ['test1', 'test2']
        res = self.post(self.url+'?token='+self.token, body=dict(names=names))
        res = json.loads(res.body.decode())
        self.assertEqual(res['errcode'], 200)
        self.assertEqual(len(res['list']), 2)
        res_names = [item['name'] for item in res['list']]
        res_names.sort()
        self.assertEqual(res_names, names)

        # delete room type
        time.sleep(2)
        rt_ids = [item['rt_id'] for item in res['list']]
        res = self.delete(self.url+'?token=%s&rt_id=%s'%(self.token, rt_ids[0]))
        res = json.loads(res.body.decode())
        self.assertEqual(res['errcode'], 200)
        time.sleep(2)
        res = self.get(self.url+'?token='+self.token)
        res = json.loads(res.body.decode())
        self.assertEqual(len(res['list']), 1)

        # update room type
        time.sleep(2)
        rt_id = rt_ids[1]
        args = {
            'rt_id': rt_id,
            'name': 'name',
            'pic': 'pic',
            'min_man': 1,
            'max_man': 10
        }
        res = self.put(self.url+'?token=%s'%self.token, body=args)
        res = json.loads(res.body.decode())
        time.sleep(2)
        res = self.get(self.url+'?token=%s'%self.token)
        res = json.loads(res.body.decode())
        self.assertEqual(res['errcode'], 200)
        self.assertEqual(len(res['list']), 1)
        for i in args:
            self.assertEqual(res['list'][0].get(i), args[i])

    def tearDown(self):
        self._clear_room_data_of_store_id(self.user['store_id'])


if __name__ == '__main__':
    unittest.main()

