#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler
from settings import STATE


class CateHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取所有的酒水分类
        '''
        cates = ctrl.cate.get_cates_ctl(self.current_user['store_id'])

        data = {
            'list': []
        }
        if not cates:
            return self.send_json(data)

        FILTER = (
            {'id': 'cate_id'},
            'store_id',
            'name',
            'update_time'
        )
        data['list'] = [utils.dict_filter(cate, FILTER) for cate in cates]
        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        添加酒水分类
        '''
        try:
            args = json.loads(self.request.body.decode())
            names = args['names']
            assert(names)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        data = {
            'cates': []
        }

        if not names:
            return self.send_json(data)

        cates = ctrl.cate.add_cates_ctl(self.current_user['store_id'], names)

        FILTER = (
            {'id': 'cate_id'},
            'store_id',
            'name',
            'update_time'
        )
        data['cates'] = [utils.dict_filter(cate, FILTER) for cate in cates]

        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        删除酒水分类
        '''
        try:
            args = json.loads(self.request.body.decode())
            cate_ids = args['cate_ids']
            assert(cate_ids)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        if not cate_ids:
            return self.send_json()

        ctrl.cate.delete_cates_ctl(self.current_user['store_id'], cate_ids)
        self.send_json()

    @erp_auth
    def put(self):
        '''
        修改某酒水分类
        '''
        try:
            cate_id = int(self.get_argument('cate_id'))
            args = json.loads(self.request.body.decode())
            name = args['name']
            assert(name)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.cate.update_cate_ctl(self.current_user['store_id'], cate_id, {
            'name': name
        })
        self.send_json()


class CateProductHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取分类下的酒水列表
        '''
        try:
            cate_id = int(self.get_argument('cate_id'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        FILTER = (
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
            'update_time'
        )
        data = {
            'list': []
        }
        products = ctrl.cate.get_cate_products_ctl(self.current_user['store_id'], cate_id)

        if not products:
            return self.send_json(data)

        data['list'] = [utils.dict_filter(product, FILTER) for product in products]
        self.send_json(data)

    @erp_auth
    def post(self):
        '''
        分类下添加酒水
        '''
        try:
            cate_id = int(self.get_argument('cate_id'))
            args = json.loads(self.request.body.decode())
            name = args['name']
            pic = args.get('pic', '')
            spec = args.get('spec', '')
            price = int(args['price'])
            unit = args['unit']
            stock = int(args['stock'])
            discount = int(args['discount'])

            assert(name and unit and discount in (0, 1))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        FILTER = (
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
            'update_time'
        )
        data = {
            'detail': {}
        }
        product = ctrl.cate.add_cate_product_ctl(self.current_user['store_id'], {
            'cate_id': cate_id,
            'name': name,
            'pic': pic,
            'price': price,
            'unit': unit,
            'spec': spec,
            'stock': stock,
            'discount': discount
        })

        data['detail'] = utils.dict_filter(product, FILTER)
        self.send_json(data)

    @erp_auth
    def delete(self):
        '''
        批量删除酒水
        '''
        try:
            args = json.loads(self.request.body.decode())
            product_ids = args['product_ids']
            for product_id in product_ids:
                assert(int(product_id))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        if not product_ids:
            return self.send_json()

        ctrl.cate.delete_cate_products_ctl(self.current_user['store_id'], product_ids)

        self.send_json()

    @erp_auth
    def put(self):
        '''
        批量修改酒水
        '''
        try:
            args = json.loads(self.request.body.decode())
            products = []
            for arg in args:
                product_id = int(arg['product_id'])
                name = arg.get('name', '')
                pic = arg.get('pic', '')
                unit = arg.get('unit', '')
                spec = arg.get('spec', '')
                price = int(arg.get('price', 0))
                stock = int(arg.get('stock', 0))
                discount = int(arg.get('discount', 0))
                state = int(arg.get('state', 0))

                assert(discount in (0, 1) and state in STATE.values())

                product = {
                    'product_id': product_id,
                    'name': name,
                    'pic': pic,
                    'unit': unit,
                    'spec': spec,
                    'discount': discount,
                    'state': state
                }

                if 'price' in arg:
                    product.update({
                        'price': price
                    })

                if 'stock' in arg:
                    product.update({
                        'stock': stock
                    })

                if 'discount' in arg:
                    product.update({
                        'discount': discount
                    })

                if 'state' in arg:
                    product.update({
                        'state': state
                    })

                products.append(product)
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        ctrl.cate.update_cate_products_ctl(self.current_user['store_id'], products)

        self.send_json()
