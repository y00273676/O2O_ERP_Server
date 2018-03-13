#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle

from settings import A_DAY


class CateCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.cate = ctrl.pdb.cate

    def __getattr__(self, name):
        return getattr(self.cate, name)

    def get_cates_key(self, store_id):
        return 't_cates_%s' % store_id

    def get_cate_product_ids_key(self, store_id, cate_id):
        return 't_cate_product_ids_%s_%s' % (store_id, cate_id)

    def add_cates(self, store_id, names):
        cates = self.cate.add_cates(store_id, names)
        key = self.get_cates_key_ctl(store_id)
        self.ctrl.rs.delete(key)
        return cates

    def get_cates(self, store_id, is_all=False):
        key = self.get_cates_key_ctl(store_id)
        cates = self.ctrl.rs.lrange(key, 0, -1)

        if cates:
            cates = [pickle.loads(cate) for cate in cates]
            if not is_all:
                cates = list(filter(lambda x: x.get('state', 2)==1, cates))
            return cates

        cates = self.cate.get_cates(store_id)
        if not cates:
            return cates

        cates_encode = [pickle.dumps(cate) for cate in cates]
        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *cates_encode).expire(key, 7 * A_DAY).execute()
        if not is_all:
            cates = list(filter(lambda x: x.get('state', 2)==1, cates))
        return cates

    def delete_cates(self, store_id, cate_ids):
        self.cate.delete_cates(store_id, cate_ids)

        key = self.get_cates_key_ctl(store_id)
        self.ctrl.rs.delete(key)

    def update_cate(self, store_id, cate_id, data):
        self.cate.update_cate(store_id, cate_id, data=data)

        key = self.get_cates_key_ctl(store_id)
        self.ctrl.rs.delete(key)

    def add_cate_product(self, store_id, data):
        data.update({
            'store_id': store_id
        })
        product = self.ctrl.pack.add_product(data)
        key = self.get_cate_product_ids_key_ctl(store_id, data['cate_id'])
        self.ctrl.rs.delete(key)
        return product

    def update_cate_products(self, store_id, products):
        for product in products:
            product_id = product.pop('product_id')
            self.ctrl.pack.update_product(store_id, product_id, data=product)
            key = self.ctrl.pack.get_product_key_ctl(product_id)
            self.ctrl.rs.delete(key)

    def delete_cate_products(self, store_id, product_ids):
        for product_id in product_ids:
            product = self.ctrl.pack.delete_product(store_id, product_id)
            if product:
                key = self.ctrl.pack.get_product_key_ctl(product_id)
                cate_key = self.get_cate_product_ids_key_ctl(store_id, product['cate_id'])
                self.ctrl.rs.delete(key, cate_key)

    def get_cate_product_ids(self, store_id, cate_id):
        key = self.get_cate_product_ids_key_ctl(store_id, cate_id)
        product_ids = self.ctrl.rs.lrange(key, 0, -1)

        if product_ids:
            return [int(pid) for pid in product_ids]

        product_ids = self.ctrl.pack.get_cate_product_ids(store_id, cate_id)
        if not product_ids:
            return product_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *product_ids).expire(key, A_DAY).execute()
        return product_ids

    def get_cate_products(self, store_id, cate_id):
        product_ids = self.get_cate_product_ids_ctl(store_id, cate_id)
        if not product_ids:
            return []
        products = self.ctrl.pack.get_products_ctl(product_ids)
        return products

