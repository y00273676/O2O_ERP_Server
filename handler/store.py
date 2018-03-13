#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import hashlib

from lib import utils
from lib.decorator import erp_auth
from control import ctrl
from handler.base import BaseHandler
from settings import VERIFY_SMS_CONTENT


class CodeHandler(BaseHandler):

    async def get(self):
        '''
        获取验证码
        '''
        try:
            phone = self.get_argument('phone')
            assert(phone)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        code = ctrl.store.gen_verify_code_ctl(phone)
        content = VERIFY_SMS_CONTENT.format(code=code)
        result = await utils.async_common_api('/verify/code/send', params=dict(phone_num=phone, content=content))

        if int(result['code']) == 0:
            self.send_json()
        else:
            raise utils.APIError(errcode=50001, errmsg=result.get('detail', '同一手机号一小时内不宜超过三次，请稍候再试'))


class VerifyHandler(BaseHandler):

    def get(self):
        '''
        校验验证码
        '''
        try:
            code = self.get_argument('code')
            phone = self.get_argument('phone')
            assert(code and phone)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        is_valid = ctrl.store.check_verify_code_ctl(phone, code)

        if is_valid:
            self.send_json()
        else:
            raise utils.APIError(errcode=50001, errmsg='验证码无效')


class SignupHandler(BaseHandler):

    def post(self):
        '''
        注册
        '''
        try:
            args = json.loads(self.request.body.decode())
            code = args.get('code')
            phone = args.get('phone')
            passwd = args.get('passwd')
            name = args.get('name')
            address = args.get('address')
            st = args.get('st')
            ed = args.get('ed')
            manager = args.get('manager', '')

            assert(code and phone)
            assert(utils.is_valid_time(st))
            assert(utils.is_valid_time(ed))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store = ctrl.store.get_store_ctl(phone)
        if store:
            raise utils.APIError(errcode=50001, errmsg='请勿重复注册')

        try:
            data = {
                'ktype': 20,
                'name': name,
                'address': address,
                'tel': phone,
                'is_test': 0,
                'is_own': 0,
                'manager': manager
            }
            ktv = utils.common_post_api('/kinfo', data)
            store_id = ktv['store_id']
            store = ctrl.store.add_store_ctl({
                        'store_id': store_id,
                        'st': st,
                        'ed': ed,
                        'name': name,
                        'phone': phone,
                        'passwd': hashlib.md5(passwd.encode()).hexdigest()
                    })
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=50001, errmsg='注册失败, 稍后再试')

        FILTER = (
            'store_id',
            'phone',
            'update_time',
            'st',
            'ed',
            'name'
        )
        store = utils.dict_filter(store, FILTER)

        self.send_json(store)


class LoginHandler(BaseHandler):

    def get(self):
        '''
        登录
        '''
        try:
            phone = self.get_argument('phone')
            passwd = self.get_argument('passwd')
            assert(phone and passwd)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        try:
            store = ctrl.store.get_store_ctl(phone)
            assert(store)
            assert(store['passwd'] == hashlib.md5(passwd.encode()).hexdigest())
            token = self._login(store)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=50001, errmsg='登录失败，请检查您的账号或密码')

        data = {}
        FILTER = (
            'store_id',
            'phone',
            'update_time',
            'st',
            'ed',
            'name'
        )
        data['store'] = utils.dict_filter(store, FILTER)
        data['token'] = token

        self.send_json(data)


class LogoutHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        退出登录
        '''
        try:
            phone = self.get_argument('phone')
            token = self.get_argument('token')
            assert(phone == self.account)
            self._logout(token)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        self.send_json()


class ResetHandler(BaseHandler):

    def post(self):
        '''
        重置密码
        '''
        try:
            args = json.loads(self.request.body.decode())
            phone = args['phone']
            passwd = args['passwd']
            code = args['code']
            assert(phone and passwd and code)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store = ctrl.store.get_store_ctl(phone)
        if not store:
            raise utils.APIError(errcode=50001, errmsg='该门店不存在')

        is_valid = ctrl.store.check_verify_code_ctl(phone, code)
        if not is_valid:
            raise utils.APIError(errcode=50001, errmsg='验证码无效')

        ctrl.store.update_store_ctl(phone, dict(passwd=hashlib.md5(passwd.encode()).hexdigest()))

        self.send_json()


class AccoutHandler(BaseHandler):

    @erp_auth
    def get(self):
        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        if not store:
            raise utils.APIError(errcode=50001, errmsg='没有门店')

        FILTER = (
            'store_id',
            'phone',
            'update_time',
            'st',
            'ed',
            'name'
        )
        store = utils.dict_filter(store, FILTER)
        ktv = utils.common_api('/kinfo/%s' % store['store_id'])
        store.update({'address': ktv.get('address', '')})
        self.send_json(dict(store=store))

    @erp_auth
    def put(self):
        try:
            args = json.loads(self.request.body.decode())
            assert args
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {}
        keys = ['name', 'st', 'ed', 'phone', 'passwd']

        if 'address' in args:
            utils.common_post_api('/kinfo/%s' % self.current_user['store_id'], dict(
                address=args['address']), method='PUT')

        for key in keys:
            if key in args:
                data.update({key: args[key]})

        if 'phone' in data:
            store = ctrl.store.get_store_ctl(data['phone'])
            if store and store['store_id']!=self.current_user['store_id']:
                raise utils.APIError(errcode=50001, errmsg='该手机号已被注册')

        if 'passwd' in data:
            store = ctrl.store.get_store_ctl(self.current_user['phone'])

            if store['passwd'] != hashlib.md5(data['passwd'].encode()).hexdigest():
                raise utils.APIError(errcode=50001, errmsg='旧密码输入错误')

            data.update({'passwd': hashlib.md5(args['newpasswd'].encode()).hexdigest()})

        if data:
            ctrl.store.update_store_ctl(self.current_user['phone'], data)
        self.send_json()

