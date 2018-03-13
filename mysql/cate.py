#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TINYINT

from settings import DB_ERP, STATE
from mysql.base import NotNullColumn, Base
from lib.decorator import models_to_list, filter_update_data


class TProductCate(Base):
    '''
    酒水品类表
    '''
    __tablename__ = 't_product_cate'

    store_id = Column(INTEGER(11))
    name = NotNullColumn(VARCHAR(128))
    order = Column(INTEGER(11), server_default='0')
    state = Column(TINYINT(1), server_default='1')            # 状态：1有效/2删除


class CateModel(object):

    def __init__(self, pdb):
        self.pdb = pdb
        self.master = pdb.get_session(DB_ERP, master=True)
        self.slave = pdb.get_session(DB_ERP)

    @models_to_list
    def add_cates(self, store_id, names):
        cates = []
        for name in names:
            if not name:
                continue
            cate = TProductCate(store_id=store_id, name=name)
            cates.append(cate)
            self.master.add(cate)
        self.master.commit()
        return cates

    @models_to_list
    def get_cates(self, store_id):
        q = self.slave.query(TProductCate).filter_by(store_id=store_id)
        return q.all()

    def delete_cates(self, store_id, cate_ids):
        data = {
            'state': STATE['delete']
        }
        q = self.master.query(TProductCate).filter_by(store_id=store_id).filter(TProductCate.id.in_(tuple(cate_ids)))
        q.update(data, synchronize_session=False)
        self.master.commit()

    @filter_update_data
    def update_cate(self, store_id, cate_id, data={}):
        q = self.master.query(TProductCate).filter_by(id=cate_id, store_id=store_id)
        q.update(data)
        self.master.commit()

