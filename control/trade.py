#!/usr/bin/env python
# -*- coding: utf-8 -*-

from settings import BILL_PAY_STATE, SERVICE_TYPE


class TradeCtrl(object):

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.trade = ctrl.pdb.order

    def __getattr__(self, name):
        return getattr(self.trade, name)

    def get_day_revenues(self, store_id, start_time, end_time):
        service_types = [SERVICE_TYPE['room'], SERVICE_TYPE['product'], SERVICE_TYPE['back']]
        revenues = self.trade.get_bills_revenue(store_id, start_time, end_time, [BILL_PAY_STATE['pay']], service_types)

        total_money = 0
        total_room_money = 0
        total_product_money = 0

        for revenue in revenues:

            total_money += revenue['money']

            if revenue['service_type'] == SERVICE_TYPE['room']:
                total_room_money += revenue['money']

            if revenue['service_type'] in (SERVICE_TYPE['product'], SERVICE_TYPE['back']):
                total_product_money += revenue['money']

        data = {
            'total_money': total_money,
            'total_room_money': total_room_money,
            'total_product_money': total_product_money
        }

        return data

    def get_day_product_sales(self, store_id, start_time, end_time, order_by, page=1, page_size=10):
        service_types = [SERVICE_TYPE['product'], SERVICE_TYPE['back']]
        revenues = self.trade.get_bills_revenue(store_id, start_time, end_time, [BILL_PAY_STATE['pay']], service_types)
        bill_ids = [revenue['id'] for revenue in revenues]

        sales = self.trade.get_product_sales(store_id, bill_ids, order_by, page, page_size)
        sales = list(filter(lambda x: x['count'], sales))

        product_ids = [sale['product_id'] for sale in sales]
        products = self.ctrl.pack.get_products_ctl(product_ids)
        products_dict = dict((product['id'], product) for product in products)

        product_cate_ids = [p['cate_id'] for p in products]
        cates = self.ctrl.cate.get_cates_ctl(store_id, is_all=True)
        id_cate_dict = {c['id']: c for c in cates}

        for sale in sales:
            product = products_dict[sale['product_id']]
            cate = id_cate_dict.get(product.get('cate_id'), {})
            sale.update({
                'name': product['name'],
                'cate_name': cate['name']
            })

        count = self.trade.get_product_sales_count(store_id, bill_ids)
        return sales, count

    def get_day_pack_sales(self, store_id, start_time, end_time, order_by, page=1, page_size=10):
        service_types = [SERVICE_TYPE['product'], SERVICE_TYPE['back']]
        revenues = self.trade.get_bills_revenue(store_id, start_time, end_time, [BILL_PAY_STATE['pay']], service_types)
        bill_ids = [revenue['id'] for revenue in revenues]

        sales = self.trade.get_pack_sales(store_id, bill_ids, order_by, page, page_size)
        sales = list(filter(lambda x: x['count'], sales))

        pack_ids = [sale['pack_id'] for sale in sales]
        packs = self.ctrl.pack.get_packs_ctl(pack_ids)
        packs_dict = dict((pack['id'], pack) for pack in packs)

        for sale in sales:
            pack = packs_dict[sale['pack_id']]
            sale.update({
                'name': pack['name']
            })

        count = self.trade.get_pack_sales_count(store_id, bill_ids)
        return sales, count

    def get_day_orders_summary(self, store_id, start_time, end_time, room_id=0, page=1, page_size=10):
        summary = self.trade.get_query_orders_summary(store_id, start_time, end_time, room_id)
        orders = self.trade.get_query_orders(store_id, start_time, end_time, room_id, page, page_size)
        [order.update({'room_name': self.ctrl.room.get_room_ctl(order.get('room_id'))['name']}) for order in orders]
        summary['total_count'] = self.trade.get_query_orders_count(store_id, start_time, end_time, room_id)
        summary['list'] = orders
        summary['total_page'] = (summary['total_count'] + page_size - 1) // page_size
        summary['page'] = page
        return summary
