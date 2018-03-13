#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TINYINT, CHAR, DATETIME
from sqlalchemy.sql.expression import func, desc

from settings import DB_ERP_ORDER, ORDER_STATE
from mysql.base import NotNullColumn, Base
from lib.decorator import model_to_dict, models_to_list, filter_update_data


class_registry = {}


class TOrder(object):
    '''
    订单表
    '''
    order_no = NotNullColumn(VARCHAR(16))                   # 订单编号
    room_id = Column(INTEGER(11), server_default='0')
    st = NotNullColumn(CHAR(16))                            # 开台时间
    ed = NotNullColumn(CHAR(16))                            # 关台时间
    minute = Column(INTEGER(11), server_default='0')        # 使用时长
    prepay = Column(INTEGER(11), server_default='0')        # 预付金额
    money = Column(INTEGER(11), server_default='0')         # 应付金额，落单后结
    real_money = Column(INTEGER(11), server_default='0')    # 实收金额，落单后结
    pay_type = Column(TINYINT(1), server_default='1')       # 支付状态：1现结/2落单后结
    describe = NotNullColumn(VARCHAR(512))
    state = Column(TINYINT(1), server_default='1')          # 状态：1进行中/2已完结
    finish_time = NotNullColumn(DATETIME, server_default='CURRENT_TIMESTAMP')
    pay_id = NotNullColumn(VARCHAR(128), server_default='')


class TBill(object):
    '''
    账单表
    '''
    order_id = Column(INTEGER(11), server_default='0')
    bill_no = NotNullColumn(VARCHAR(18))                    # 流水号
    room_id = Column(INTEGER(11), server_default='0')
    money = Column(INTEGER(11), server_default='0')
    real_money = Column(INTEGER(11), server_default='0')
    rate = Column(INTEGER(11), server_default='100')
    pay_md = Column(TINYINT(1), server_default='1')         # 支付方式
    pay_state = Column(TINYINT(1), server_default='0')      # 支付状态：0未付/1已付/2取消
    service_type = Column(TINYINT(1), server_default='1')   # 业务类型：1房费/2酒水/3预付/4退单
    describe = NotNullColumn(VARCHAR(512))
    pay_id = NotNullColumn(VARCHAR(128))
    extra = NotNullColumn(VARCHAR(128), server_default='{}')  # 存各类账单特有的数据 {'minute': 10}


class TBillRoom(object):
    '''
    房费账单表
    '''
    order_id = Column(INTEGER(11), server_default='0')
    bill_id = Column(INTEGER(11), server_default='0')       # 账单ID
    room_id = Column(INTEGER(11), server_default='0')
    fee_id = Column(INTEGER(11), server_default='0')        # 计费方式ID
    pack_id = Column(INTEGER(11), server_default='0')       # 套餐ID
    st = NotNullColumn(CHAR(16))                            # 开始时间
    ed = NotNullColumn(CHAR(16))                            # 结束时间
    minute = Column(INTEGER(11), server_default='0')        # 消费时长
    money = Column(INTEGER(11), server_default='0')         # 金额
    md = Column(TINYINT(1), server_default='1')             # 计费方式：1计时/2套餐


class TBillProduct(object):
    '''
    酒水账单表
    '''
    order_id = Column(INTEGER(11), server_default='0')
    bill_id = Column(INTEGER(11), server_default='0')       # 账单ID
    room_id = Column(INTEGER(11), server_default='0')
    product_id = Column(INTEGER(11), server_default='0')    # 商品ID
    pack_id = Column(INTEGER(11), server_default='0')       # 套餐ID
    count = Column(INTEGER(11), server_default='0')         # 数量
    unit = NotNullColumn(VARCHAR(16))                       # 单位
    money = Column(INTEGER(11), server_default='0')         # 金额，单位：分
    md = Column(TINYINT(1), server_default='1')             # 酒水类型：1单品/2套餐


def get_model(table_name, store_id):
    table_map = {
        't_order': TOrder,
        't_bill': TBill,
        't_bill_room': TBillRoom,
        't_bill_product': TBillProduct
    }

    model = table_map[table_name]
    table_name = '%s_%s' % (table_name, store_id)
    model_name = '%s_%s' % (model.__name__, store_id)

    if model_name not in class_registry:
        model = type(model_name, (model, Base), {
            '__tablename__': table_name
        })
        class_registry[model_name] = model
    else:
        model = class_registry[model_name]

    return model


class OrderModel(object):

    def __init__(self, pdb):
        self.pdb = pdb
        self.master = pdb.get_session(DB_ERP_ORDER, master=True)
        self.slave = pdb.get_session(DB_ERP_ORDER)

    @models_to_list
    def get_using_orders(self, store_id, room_ids):
        if not room_ids:
            return []
        OrderModel = get_model('t_order', store_id)
        q = self.slave.query(OrderModel)
        q = q.filter(OrderModel.room_id.in_(tuple(room_ids))).filter_by(state=ORDER_STATE['using'])
        return q.all()

    @model_to_dict
    def add_order(self, store_id, data):
        OrderModel = get_model('t_order', store_id)
        order = OrderModel(**data)
        self.master.add(order)
        self.master.commit()
        return order

    @filter_update_data
    def update_order(self, store_id, order_no, data={}):
        OrderModel = get_model('t_order', store_id)
        q = self.master.query(OrderModel).filter_by(order_no=order_no)
        q.update(data)
        self.master.commit()

    @models_to_list
    def get_orders(self, store_id, order_nos):
        OrderModel = get_model('t_order', store_id)
        q = self.master.query(OrderModel).filter(OrderModel.order_no.in_(order_nos))
        return q.all()

    @model_to_dict
    def add_bill(self, store_id, data):
        BillModel = get_model('t_bill', store_id)
        bill = BillModel(**data)
        self.master.add(bill)
        self.master.commit()
        return bill

    @filter_update_data
    def update_bill(self, store_id, bill_id, data={}):
        BillModel = get_model('t_bill', store_id)
        q = self.master.query(BillModel).filter_by(id=bill_id)
        q.update(data)
        self.master.commit()

    def add_bill_room(self, store_id, bills):
        BillRoomModel = get_model('t_bill_room', store_id)
        for bill in bills:
            bill = BillRoomModel(**bill)
            self.master.add(bill)
        self.master.commit()

    def add_bill_product(self, store_id, products, packs):
        BillProductModel = get_model('t_bill_product', store_id)
        for product in products:
            bill = BillProductModel(**product)
            self.master.add(bill)
        for pack in packs:
            bill = BillProductModel(**pack)
            self.master.add(bill)
        self.master.commit()

    def get_order_bill_ids(self, store_id, order_id):
        BillModel = get_model('t_bill', store_id)
        q = self.slave.query(BillModel.id).filter_by(order_id=order_id)
        bills = q.all()
        return [int(bill.id) for bill in bills]

    @models_to_list
    def get_bills(self, store_id, bill_ids):
        if not bill_ids:
            return []
        BillModel = get_model('t_bill', store_id)
        q = self.master.query(BillModel)
        q = q.filter(BillModel.id.in_(tuple(bill_ids)))
        return q.all()

    @models_to_list
    def get_bills_revenue(self, store_id, start_time, end_time, pay_states=[], service_types=[]):
        BillModel = get_model('t_bill', store_id)
        q = self.slave.query(BillModel)
        q = q.filter(BillModel.pay_state.in_(tuple(pay_states)))
        q = q.filter(BillModel.service_type.in_(tuple(service_types)))
        q = q.filter(BillModel.update_time >= start_time, BillModel.update_time <= end_time)
        return q.all()

    def get_order_bill_room_ids(self, store_id, order_id):
        BillModel = get_model('t_bill_room', store_id)
        q = self.slave.query(BillModel.id).filter_by(order_id=order_id)
        bills = q.all()
        return [int(bill.id) for bill in bills]

    @models_to_list
    def get_bills_room(self, store_id, br_ids):
        if not br_ids:
            return []
        BillModel = get_model('t_bill_room', store_id)
        q = self.slave.query(BillModel)
        q = q.filter(BillModel.id.in_(tuple(br_ids)))
        return q.all()

    def get_order_bill_product_ids(self, store_id, order_id):
        BillModel = get_model('t_bill_product', store_id)
        q = self.slave.query(BillModel.id).filter_by(order_id=order_id)
        bills = q.all()
        return [int(bill.id) for bill in bills]

    @models_to_list
    def get_bills_product(self, store_id, bp_ids):
        if not bp_ids:
            return []
        BillModel = get_model('t_bill_product', store_id)
        q = self.slave.query(BillModel)
        q = q.filter(BillModel.id.in_(tuple(bp_ids)))
        return q.all()

    def get_product_sales(self, store_id, bill_ids, order_by='count', page=1, page_size=10):
        if not bill_ids:
            return []
        offset = (page - 1) * page_size
        BillModel = get_model('t_bill_product', store_id)
        q = self.slave.query(BillModel.product_id, func.sum(BillModel.count).label('count'), func.sum(BillModel.money).label('money'))
        q = q.filter(BillModel.bill_id.in_(tuple(bill_ids)), BillModel.product_id > 0)
        q = q.group_by('product_id').order_by(desc(order_by)).offset(offset).limit(page_size)
        result = q.all()
        sales = []
        for ret in result:
            sales.append({
                'product_id': ret.product_id,
                'count': int(ret.count) if ret.count else 0,
                'money': int(ret.money) if ret.money else 0
            })
        return sales

    def get_product_sales_count(self, store_id, bill_ids):
        BillModel = get_model('t_bill_product', store_id)
        q = self.slave.query(BillModel)
        q = q.filter(BillModel.bill_id.in_(tuple(bill_ids)), BillModel.product_id > 0)
        q = q.group_by('product_id')
        count = q.count()
        return int(count) if count else 0

    def get_pack_sales(self, store_id, bill_ids, order_by='count', page=1, page_size=10):
        if not bill_ids:
            return []
        offset = (page - 1) * page_size
        BillModel = get_model('t_bill_product', store_id)
        q = self.slave.query(BillModel.pack_id, func.sum(BillModel.count).label('count'), func.sum(BillModel.money).label('money'))
        q = q.filter(BillModel.bill_id.in_(tuple(bill_ids)), BillModel.pack_id > 0)
        q = q.group_by('pack_id').order_by(desc(order_by)).offset(offset).limit(page_size)
        result = q.all()
        sales = []
        for ret in result:
            sales.append({
                'pack_id': ret.pack_id,
                'count': int(ret.count) if ret.count else 0,
                'money': int(ret.money) if ret.money else 0
            })
        return sales

    def get_pack_sales_count(self, store_id, bill_ids):
        BillModel = get_model('t_bill_product', store_id)
        q = self.slave.query(BillModel)
        q = q.filter(BillModel.bill_id.in_(tuple(bill_ids)), BillModel.pack_id > 0)
        q = q.group_by('pack_id')
        count = q.count()
        return int(count) if count else 0

    @models_to_list
    def get_query_orders(self, store_id, start_time, end_time, room_id=0, page=1, page_size=10, is_total=False):
        offset = (page - 1) * page_size
        OrderModel = get_model('t_order', store_id)
        q = self.slave.query(OrderModel)
        q = q.filter_by(state=ORDER_STATE['finish'])
        q = q.filter(OrderModel.finish_time >= start_time, OrderModel.finish_time <= end_time)
        if room_id:
            q = q.filter_by(room_id=room_id)
        q = q.order_by(desc('finish_time'))
        if not is_total:
            q = q.offset(offset).limit(page_size)
        orders = q.all()
        return orders

    def get_query_orders_count(self, store_id, start_time, end_time, room_id=0):
        OrderModel = get_model('t_order', store_id)
        q = self.slave.query(func.sum('1').label('count')).select_from(OrderModel)
        q = q.filter_by(state=ORDER_STATE['finish'])
        q = q.filter(OrderModel.finish_time >= start_time, OrderModel.finish_time <= end_time)
        if room_id:
            q = q.filter_by(room_id=room_id)
        count = q.scalar()
        return int(count) if count else 0

    def get_query_orders_summary(self, store_id, start_time, end_time, room_id=0):
        OrderModel = get_model('t_order', store_id)
        q = self.slave.query(func.count('1').label('count'), func.sum(OrderModel.money).label('money'), func.sum(OrderModel.real_money).label('real_money'))
        if room_id:
            q = q.filter_by(room_id=room_id)
        q = q.filter(OrderModel.state == ORDER_STATE['finish'])
        q = q.filter(OrderModel.finish_time >= start_time, OrderModel.finish_time <= end_time)
        result = q.all()

        summary = {
            'count': 0,
            'money': 0,
            'real_money': 0
        }

        if not result:
            return summary

        if result[0].count:
            summary['count'] = result[0].count
        if result[0].money:
            summary['money'] = int(result[0].money)
        if result[0].real_money:
            summary['real_money'] = int(result[0].real_money)

        return summary

