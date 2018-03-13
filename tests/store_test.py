import unittest
import json
import time
import subprocess
import pdb

from pprint import pprint
from tests import AsyncHTTPTestCase, current_time_str


class StoreTest(AsyncHTTPTestCase):

    def test_fetch_code(self):
        # res = self.get('/store/code', params=dict(phone='15990187931'))
        # res = json.loads(res.body.decode())
        # self.assertEquals(200, res['errcode'])
        pass


