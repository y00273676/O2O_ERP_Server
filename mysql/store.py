#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TINYINT, CHAR

from settings import DB_ERP
from mysql.base import NotNullColumn, Base
from lib.decorator import model_to_dict, filter_update_data, models_to_list


class TStore(Base):
    '''
    商户表
    '''
    __tablename__ = 't_store'

    store_id = Column(INTEGER(11))
    name = NotNullColumn(VARCHAR(128))
    st = NotNullColumn(CHAR(5))
    ed = NotNullColumn(CHAR(5))
    phone = NotNullColumn(VARCHAR(32))
    passwd = NotNullColumn(VARCHAR(32))
    status = NotNullColumn(TINYINT(1))


class StoreModel(object):

    def __init__(self, pdb):
        self.pdb = pdb
        self.master = pdb.get_session(DB_ERP, master=True)
        self.slave = pdb.get_session(DB_ERP)

    @model_to_dict
    def get_store(self, key, t='phone'):
        q = self.slave.query(TStore)
        if t == 'store_id':
            q = q.filter_by(store_id=key)
        elif t == 'phone':
            q = q.filter_by(phone=key)
        return q.first()

    @model_to_dict
    def add_store(self, **data):
        store = TStore(**data)
        self.master.add(store)
        self.master.commit()
        return store

    @filter_update_data
    def update_store(self, key, t='phone', data={}):
        q = self.master.query(TStore)
        if t == 'store_id':
            q = q.filter_by(store_id=key)
        elif t == 'phone':
            q = q.filter_by(phone=key)
        q.update(data)
        self.master.commit()

    @models_to_list
    def get_latest_stores(self):
        thirty_min_ago = str(datetime.datetime.now() - datetime.timedelta(seconds=30*60))
        return self.slave.query(TStore).filter(TStore.create_time>thirty_min_ago).all()

