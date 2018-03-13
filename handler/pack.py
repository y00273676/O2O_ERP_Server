#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler


class ProductHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取某酒水套餐下的所有酒水列表
        '''
        try:
            pack_id = int(self.get_argument('pack_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        pack, products = ctrl.pack.get_pack_info_ctl(self.current_user['store_id'], pack_id)

        data = {
            'detail': {}
        }

        if not pack:
            return self.send_json(data)

        PACK_FILTER = (
            {'id': 'pack_id'},
            'store_id',
            'name',
            'start_date',
            'end_date',
            'pic',
            'price',
            'day',
            'rt_ids',
            'st',
            'ed',
            'state',
            'hour',
            'md',
            'update_time'
        )
        PRODUCT_FILTER = (
            {'id': 'product_id'},
            'store_id',
            'cate_id',
            'name',
            'pic',
            'price',
            'unit',
            'spec',
            'stock',
            'discount',
            'state',
            'order',
            'count',
            'update_time'
        )
        pack = utils.dict_filter(pack, PACK_FILTER)
        products = [utils.dict_filter(product, PRODUCT_FILTER) for product in products]
        data['detail'] = pack
        data['detail']['list'] = products

        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        往某套餐下添加酒水
        '''
        try:
            pack_id = int(self.get_argument('pack_id'))
            args = json.loads(self.request.body.decode())
            products = []
            for arg in args:
                product_id = int(arg['product_id'])
                count = int(arg['count'])
                products.append({
                    'product_id': product_id,
                    'count': count
                })
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.pack.add_pack_products_ctl(self.current_user['store_id'], pack_id, products)

        self.send_json()

    @erp_auth
    def delete(self):
        '''
        删除某套餐下的酒水
        '''
        try:
            pack_id = int(self.get_argument('pack_id'))
            product_id = int(self.get_argument('product_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.pack.delete_pack_product_ctl(self.current_user['store_id'], pack_id, product_id)
        self.send_json()


class PackHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取歌厅所有的酒水套餐
        '''
        packs = ctrl.pack.get_store_packs_ctl(self.current_user['store_id'])

        data = {
            'list': []
        }

        if not packs:
            return self.send_json(data)

        FILTER = (
            {'id': 'pack_id'},
            'name',
            'start_date',
            'end_date',
            'pic',
            'price',
            'day',
            'rt_ids',
            'st',
            'ed',
            'state',
            'update_time'
        )

        data['list'] = [utils.dict_filter(pack, FILTER) for pack in packs]
        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        添加酒水套餐
        '''
        try:
            args = json.loads(self.request.body.decode())
            name = args['name']
            start_date = args['start_date']
            end_date = args['end_date']
            price = int(args['price'])
            pic = args.get('pic', '')
            day = args['day']
            rt_ids = args['rt_ids']
            st = args['st']
            ed = args['ed']
            products = args.get('list', [])

            assert(utils.is_valid_day_value(day))
            assert(utils.is_valid_rt_ids_value(rt_ids))
            assert(utils.is_valid_time(st))
            assert(utils.is_valid_time(ed))
            assert(price > 0)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        FILTER = (
            {'id': 'pack_id'},
            'name',
            'start_date',
            'end_date',
            'pic',
            'price',
            'day',
            'rt_ids',
            'st',
            'ed',
            'state',
            'update_time'
        )
        data = {
            'detail': {}
        }
        pack = ctrl.pack.add_store_pack_ctl(self.current_user['store_id'], products, {
            'name': name,
            'start_date': start_date,
            'end_date': end_date,
            'price': price,
            'pic': pic,
            'day': day,
            'rt_ids': rt_ids,
            'st': st,
            'ed': ed
        })
        data['detail'] = utils.dict_filter(pack, FILTER)

        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        批量删除酒水套餐
        '''
        try:
            args = json.loads(self.request.body.decode())
            pack_ids = args['pack_ids']
            for pack_id in pack_ids:
                assert(int(pack_id))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        if not pack_ids:
            return self.send_json()

        ctrl.pack.delete_packs_ctl(self.current_user['store_id'], pack_ids)
        self.send_json()

    @erp_auth
    def put(self):
        '''
        批量修改酒水套餐
        '''
        try:
            args = json.loads(self.request.body.decode())
            packs = []
            for arg in args:
                pack_id = int(arg['pack_id'])
                name = arg.get('name', '')
                start_date = arg.get('start_date', '')
                end_date = arg.get('end_date', '')
                pic = arg.get('pic', '')
                day = arg.get('day', '')
                rt_ids = arg.get('rt_ids', '')
                st = arg.get('st', '')
                ed = arg.get('ed', '')
                price = int(arg.get('price', 0))
                state = int(arg.get('state', 0))

                assert(utils.is_valid_date(start_date))
                assert(utils.is_valid_date(end_date))
                assert(utils.is_valid_rt_ids_value(rt_ids))
                assert(utils.is_valid_time(st))
                assert(utils.is_valid_time(ed))
                assert(price >= 0 and state in (0, 1))

                pack = {
                    'pack_id': pack_id,
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'pic': pic,
                    'day': day,
                    'rt_ids': rt_ids,
                    'st': st,
                    'ed': ed
                }

                if 'price' in arg:
                    pack.update({
                        'price': price
                    })

                if 'state' in arg:
                    pack.update({
                        'state': state
                    })

                packs.append(pack)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.pack.update_packs_ctl(self.current_user['store_id'], packs)

        self.send_json()
