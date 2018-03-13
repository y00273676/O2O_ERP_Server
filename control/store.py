#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import random

from settings import A_DAY
from lib import utils


class StoreCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.store = ctrl.pdb.store

    def __getattr__(self, name):
        return getattr(self.store, name)

    def get_store_key(self, phone):
        return 't_store_%s' % phone

    def get_verify_code_send_times_key(self, phone):
        return 'verify_send_times_%s' % phone

    def get_verify_code_key(self, phone):
        return 'verify_code_%s' % phone

    def get_store(self, phone):
        key = self.get_store_key_ctl(phone)
        store = self.ctrl.rs.get(key)

        if store:
            return pickle.loads(store)

        store = self.store.get_store(phone)
        if store:
            self.ctrl.rs.set(key, pickle.dumps(store), A_DAY)

        return store

    def update_store(self, phone, data):
        self.store.update_store(phone, data=data)
        key = self.get_store_key_ctl(phone)
        self.ctrl.rs.delete(key)

    def add_store(self, data):
        phone = data['phone']
        store = self.store.add_store(**data)
        key = self.get_store_key_ctl(phone)
        self.ctrl.rs.delete(key)
        return store

    def gen_verify_code(self, phone):
        send_times_key = self.get_verify_code_send_times_key_ctl(phone)
        send_times = self.ctrl.rs.get(send_times_key)

        if send_times and int(send_times.decode()) >= 5:
            raise utils.APIError(errcode=50001, errmsg='验证码发送超额')

        key = self.get_verify_code_key_ctl(phone)
        code = '%06d' % random.randint(0, 999999)
        self.ctrl.rs.set(key, code, 5 * 60)

        if send_times:
            self.ctrl.rs.incr(send_times_key)
        else:
            self.ctrl.rs.set(send_times_key, 1, utils.seconds_to_midnight())

        return code

    def check_verify_code(self, phone, code):
        key = self.get_verify_code_key_ctl(phone)
        exist_code = self.ctrl.rs.get(key)

        if not exist_code:
            return False

        return exist_code.decode() == code
