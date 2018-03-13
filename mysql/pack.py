#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TINYINT, CHAR, DATE, ENUM

from settings import DB_ERP, STATE
from mysql.base import NotNullColumn, Base
from lib.decorator import model_to_dict, models_to_list, filter_update_data


class TProduct(Base):
    '''
    酒水单品
    '''
    __tablename__ = 't_product'

    store_id = Column(INTEGER(11))
    cate_id = Column(INTEGER(11), server_default='0')
    name = NotNullColumn(VARCHAR(128))
    pic = NotNullColumn(VARCHAR(256))
    price = Column(INTEGER(11), server_default='0')
    unit = NotNullColumn(VARCHAR(16))
    spec = NotNullColumn(VARCHAR(64))
    stock = Column(INTEGER(11), server_default='0')
    discount = Column(TINYINT(1), server_default='0')
    state = Column(TINYINT(1), server_default='1')           # 0下架/1上架/2删除
    order = Column(INTEGER(11), server_default='1')


class TPack(Base):
    '''
    酒水套餐
    '''
    __tablename__ = 't_pack'

    store_id = Column(INTEGER(11))
    name = NotNullColumn(VARCHAR(128))
    start_date = NotNullColumn(DATE)
    end_date = NotNullColumn(DATE)
    pic = NotNullColumn(VARCHAR(256))
    price = Column(INTEGER(11), server_default='0')
    day = NotNullColumn(VARCHAR(32))
    rt_ids = NotNullColumn(VARCHAR(128))
    st = Column(CHAR(5), server_default='')
    ed = Column(CHAR(5), server_default='')
    state = NotNullColumn(TINYINT(1))                        # 0下架/1上架/2删除
    hour = Column(INTEGER(11), server_default='0')
    md = NotNullColumn(ENUM('room', 'product'))              # 包房套餐/普通酒水套餐


class TPackProduct(Base):
    '''
    酒水套餐下包含的酒水列表
    '''
    __tablename__ = 't_pack_product'

    store_id = Column(INTEGER(11))
    pack_id = Column(INTEGER(11), server_default='0')
    product_id = Column(INTEGER(11), server_default='0')
    count = Column(INTEGER(11), server_default='0')
    state = NotNullColumn(TINYINT(1))                        # 1有效/2删除


class PackModel(object):

    def __init__(self, pdb):
        self.pdb = pdb
        self.master = pdb.get_session(DB_ERP, master=True)
        self.slave = pdb.get_session(DB_ERP)

    def get_cate_product_ids(self, store_id, cate_id):
        q = self.slave.query(TProduct).filter_by(store_id=store_id, cate_id=cate_id)
        q = q.filter(TProduct.state.in_([STATE['unvalid'], STATE['valid']]))
        q = q.order_by(TProduct.state.desc())
        products = q.all()
        return [int(product.id) for product in products]

    @model_to_dict
    def add_product(self, data):
        product = TProduct(**data)
        self.master.add(product)
        self.master.commit()
        return product

    @filter_update_data
    def update_product(self, store_id, product_id, data={}):
        q = self.master.query(TProduct).filter_by(id=product_id, store_id=store_id)
        q.update(data)
        self.master.commit()

    @model_to_dict
    def delete_product(self, store_id, product_id):
        q = self.master.query(TProduct).filter_by(id=product_id, store_id=store_id)
        product = q.scalar()
        q.update({
            'state': STATE['delete']
        })
        self.master.commit()
        return product

    def delete_pack(self, store_id, pack_id):
        data = {
            'state': STATE['delete']
        }
        self.master.query(TPack).filter_by(id=pack_id).update(data)
        self.master.query(TPackProduct).filter_by(store_id=store_id, pack_id=pack_id).update(data, synchronize_session=False)
        self.master.commit()

    @model_to_dict
    def add_pack(self, data):
        pack = TPack(**data)
        self.master.add(pack)
        self.master.commit()
        return pack

    def add_pack_products(self, store_id, pack_id, products):
        for pdc in products:
            if not pdc:
                continue

            count = pdc['count']
            product_id = pdc['product_id']

            q = self.master.query(TPackProduct).filter_by(store_id=store_id, pack_id=pack_id, product_id=product_id)

            if q.scalar():
                q.update({
                    'count': count
                })
            else:
                pack = TPackProduct(store_id=store_id, pack_id=pack_id,
                                    product_id=product_id, count=count)
                self.master.add(pack)

        self.master.commit()

    @models_to_list
    def get_pack_products(self, store_id, pack_id):
        q = self.slave.query(TPackProduct).filter_by(store_id=store_id, pack_id=pack_id, state=STATE['valid'])
        return q.all()

    def delete_pack_product(self, store_id, pack_id, product_id):
        data = {
            'state': STATE['delete']
        }
        self.master.query(TPackProduct).filter_by(store_id=store_id, pack_id=pack_id, product_id=product_id).update(data)
        self.master.query(TProduct).filter_by(id=product_id).update(data)
        self.master.commit()

    @filter_update_data
    def update_pack(self, store_id, pack_id, data={}):
        q = self.master.query(TPack).filter_by(id=pack_id, store_id=store_id)
        q.update(data)
        self.master.commit()

    @models_to_list
    def get_products(self, product_ids):
        q = self.slave.query(TProduct).filter(TProduct.id.in_(product_ids))
        return q.all()

    @models_to_list
    def get_packs(self, pack_ids):
        q = self.slave.query(TPack).filter(TPack.id.in_(pack_ids))
        return q.all()

    def get_store_pack_ids(self, store_id):
        q = self.slave.query(TPack.id).filter_by(store_id=store_id, md='product')
        q = q.filter(TPack.state.in_([STATE['unvalid'], STATE['valid']]))
        q = q.order_by(TPack.state.desc())
        packs = q.all()
        return [int(pack.id) for pack in packs]
