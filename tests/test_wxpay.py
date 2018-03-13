import unittest
import json
import time
import subprocess
import pdb

from pprint import pprint
from tests import AsyncHTTPTestCase, current_time_str


class CouponPayTests(AsyncHTTPTestCase):

    def get_mac(self, mac_id=''):
        params = {'mac_id': '00E07E006264' if not mac_id else mac_id}
        r = self.get('/bar/info', params=params)
        self.assertEqual(200, r.code)
        jr = json.loads(r.body.decode())
        pprint(jr)
        return jr['info']

    def post_pay(self, mac_id='', fee=100, info='测试wow支付'):
        mac=self.get_mac(mac_id)

        params = {
            'tp': 1,
            'sp_id': mac['sp_id'],
            'store_id': mac['store_id'],
            'mac_id': mac['mac_id'],
            'pay_fee': fee,
            'pay_coin': 0,
            'info': info,
        }
        r = self.post('/v2/bar/order', body=params)
        self.assertEqual(200, r.code)
        jr = json.loads(r.body.decode())
        pprint(jr)
        self.assertEqual(200, jr['errcode'])
        self.assertIn('order_id', jr)
        self.order_id=jr['order_id']
        self.assertEqual(200, jr['errcode'])
        self.assertIn('pay_url', jr)
        pprint(jr['pay_url'])
        subprocess.run(['qr', jr['pay_url']])
        pdb.set_trace()
        # self.assertIn('prepay_id', jr)
        return jr['order_id']

    def query_pay(self, order_id):
        params = {'order_id': order_id}
        r = self.get('/v2/bar/order/query', params=params)
        self.assertEqual(200, r.code)
        jr = json.loads(r.body.decode())
        pprint(jr)
        self.assertEqual(200, jr['errcode'])
        self.assertEqual(1, jr['is_payed'])

    def close_pay(self, order_id):
        params = {'order_id': order_id}
        r = self.get('/v2/bar/order/close', params=params)
        self.assertEqual(200, r.code)
        jr = json.loads(r.body.decode())
        pprint(jr)
        self.assertEqual(200, jr['errcode'])
        self.assertEqual(0, jr['is_closed'])
        return jr

    def test_pay(self):
        pprint('支付0.01元')
        order_id = self.post_pay(fee=1)
        self.query_pay(order_id)
        jr = self.close_pay(order_id)


if __name__ == '__main__':
    unittest.main()
