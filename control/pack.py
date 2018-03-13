#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle

from settings import A_DAY


class PackCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.pack = ctrl.pdb.pack

    def __getattr__(self, name):
        return getattr(self.pack, name)

    def get_pack_key(self, pack_id):
        return 't_pack_%s' % pack_id

    def get_product_key(self, product_id):
        return 't_product_%s' % product_id

    def get_pack_products_key(self, store_id, pack_id):
        return 't_pack_products_%s_%s' % (store_id, pack_id)

    def get_store_pack_ids_key(self, store_id):
        return 't_store_pack_ids_%s' % store_id

    def get_products(self, pids=[]):
        if not pids:
            return []

        multi_key = [self.get_product_key_ctl(pid) for pid in pids]
        cached = [pickle.loads(item) if item else None for item in self.ctrl.rs.mget(multi_key)]
        multi_product = dict(zip(multi_key, cached))
        miss_pids = [pid for pid in pids if multi_product[self.get_product_key_ctl(pid)] is None]
        if not miss_pids:
            return [multi_product[self.get_product_key_ctl(pid)] for pid in pids]

        miss_product_list = self.pack.get_products(tuple(miss_pids))
        miss_pids = [miss_product['id'] for miss_product in miss_product_list]
        miss_multi_key = [self.get_product_key_ctl(pid) for pid in miss_pids]
        miss_product = dict(zip(miss_multi_key, miss_product_list))

        if miss_product:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_product_encode = dict((key, pickle.dumps(miss_product[key])) for key in miss_product)
            pl.mset(miss_product_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_product.update(miss_product)
        return [multi_product[self.get_product_key_ctl(pid)] for pid in pids if self.get_product_key_ctl(pid) in multi_product]

    def get_packs(self, pkids=[]):
        if not pkids:
            return []

        multi_key = [self.get_pack_key_ctl(pid) for pid in pkids]
        cached = self.ctrl.rs.mget(multi_key)
        cached = [pickle.loads(item) if item else None for item in cached]
        multi_pack = dict(zip(multi_key, cached))
        miss_pids = [pid for pid in pkids if multi_pack[self.get_pack_key_ctl(pid)] is None]
        if not miss_pids:
            return [multi_pack[self.get_pack_key_ctl(pid)] for pid in pkids]

        miss_pack_list = self.pack.get_packs(tuple(miss_pids))
        miss_pids = [miss_pack['id'] for miss_pack in miss_pack_list]
        miss_multi_key = [self.get_pack_key_ctl(pid) for pid in miss_pids]
        miss_pack = dict(zip(miss_multi_key, miss_pack_list))

        if miss_pack:
            pl = self.ctrl.rs.pipeline(transaction=True)
            miss_pack_encode = dict((key, pickle.dumps(miss_pack[key])) for key in miss_pack)
            pl.mset(miss_pack_encode)
            for key in miss_multi_key:
                pl.expire(key, A_DAY)
            pl.execute()

        multi_pack.update(miss_pack)
        return [multi_pack[self.get_pack_key_ctl(pid)] for pid in pkids if self.get_pack_key_ctl(pid) in multi_pack]

    def get_pack(self, pack_id):
        packs = self.get_packs_ctl([pack_id])
        if not packs:
            return {}
        return packs[0]

    def update_pack(self, store_id, pack_id, data):
        self.pack.update_pack(store_id, pack_id, data=data)
        key = self.get_pack_key_ctl(pack_id)
        self.ctrl.rs.delete(key)

    def update_packs(self, store_id, packs):
        for pack in packs:
            pack_id = pack.pop('pack_id')
            self.update_pack_ctl(store_id, pack_id, pack)

    def get_pack_info(self, store_id, pack_id):
        pack = self.get_pack_ctl(pack_id)
        if not pack:
            return {}, []

        pack_id = pack['id']

        pack_pts = self.get_pack_products_ctl(store_id, pack_id)

        if not pack_pts:
            return pack, []

        product_ids = [int(pt['product_id']) for pt in pack_pts]
        products = self.get_products_ctl(product_ids)

        pack_pts_dict = dict((p['product_id'], p) for p in pack_pts)

        for product in products:
            product['count'] = pack_pts_dict[product['id']]['count']

        return pack, products

    def delete_pack_product(self, store_id, pack_id, product_id):
        self.pack.delete_pack_product(store_id, pack_id, product_id)
        pack_key = self.get_pack_products_key_ctl(store_id, pack_id)
        product_key = self.get_product_key_ctl(product_id)
        self.ctrl.rs.delete(pack_key, product_key)

    def add_pack_products(self, store_id, pack_id, products):
        pts_dict = dict((int(p['product_id']), p) for p in products)
        product_ids = pts_dict.keys()

        if not product_ids:
            return

        products = self.get_products_ctl(product_ids)
        valid_products = [pts_dict[product['id']] for product in products]

        if valid_products:
            self.pack.add_pack_products(store_id, pack_id, valid_products)
            pack_key = self.get_pack_products_key_ctl(store_id, pack_id)
            self.ctrl.rs.delete(pack_key)

    def get_pack_products(self, store_id, pack_id):
        key = self.get_pack_products_key_ctl(store_id, pack_id)
        pack_products = self.ctrl.rs.lrange(key, 0, -1)

        if pack_products:
            pack_products = [pickle.loads(pack) for pack in pack_products]
            return pack_products

        pack_products = self.pack.get_pack_products(store_id, pack_id)
        if not pack_products:
            return pack_products

        pack_products_encode = [pickle.dumps(pack) for pack in pack_products]
        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *pack_products_encode).expire(key, A_DAY).execute()
        return pack_products

    def get_store_pack_ids(self, store_id):
        key = self.get_store_pack_ids_key_ctl(store_id)
        pack_ids = self.ctrl.rs.lrange(key, 0, -1)

        if pack_ids:
            return [int(pid) for pid in pack_ids]

        pack_ids = self.pack.get_store_pack_ids(store_id)
        if not pack_ids:
            return pack_ids

        pl = self.ctrl.rs.pipeline(transaction=True)
        pl.rpush(key, *pack_ids).expire(key, A_DAY).execute()
        return pack_ids

    def get_store_packs(self, store_id):
        pack_ids = self.get_store_pack_ids_ctl(store_id)
        packs = self.get_packs_ctl(pack_ids)
        return packs

    def add_store_pack(self, store_id, products, data):
        data.update({
            'store_id': store_id
        })

        id_count_dict = {}
        [id_count_dict.update({int(i['product_id']): int(i['count'])}) for i in products]
        pack = self.pack.add_pack(data)
        pack_id = pack['id']
        product_ids = [product['product_id'] for product in products]
        products = self.get_products_ctl(product_ids)
        [p.update({'count': id_count_dict[p['id']], 'product_id': p['id']}) for p in products]
        self.pack.add_pack_products(store_id, pack_id, products)

        key = self.get_store_pack_ids_key_ctl(store_id)
        self.ctrl.rs.delete(key)
        return pack

    def delete_pack(self, store_id, pack_id):
        self.pack.delete_pack(store_id, pack_id)

        key = self.get_store_pack_ids_key_ctl(store_id)
        pack_key = self.get_pack_key_ctl(pack_id)
        self.ctrl.rs.delete(key, pack_key)

    def delete_packs(self, store_id, pack_ids):
        for pack_id in pack_ids:
            self.delete_pack_ctl(store_id, pack_id)

