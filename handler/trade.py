#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import arrow
import logging

from lib import utils
from control import ctrl
from lib.decorator import erp_auth
from handler.base import BaseHandler


class StatRevenueHandler(BaseHandler):

    def get_day_revenues(self, store_id, day):
        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        st = store['st']
        ed = store['ed']

        if day == 'today':
            start_time, end_time = utils.get_today_start_end_time(st, ed)
        elif day == 'yesterday':
            start_time, end_time = utils.get_yesterday_start_end_time(st, ed)
        elif day == '7days':
            start_time, end_time = utils.get_7days_start_end_time(st, ed)
        else:
            start_time, end_time = utils.get_30days_start_end_time(st, ed)

        revenue = ctrl.trade.get_day_revenues_ctl(store_id, start_time, end_time)

        self.send_json({
            'revenue': revenue
        })

    def get_query_revenues(self, store_id, start_day, end_day):
        try:
            start_day = arrow.get(start_day, 'YYYY-MM-DD')
            end_day = arrow.get(end_day, 'YYYY-MM-DD')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001, errmsg='日期格式不合法')

        if start_day > end_day:
            raise utils.APIError(errcode=10001, errmsg='起始日期不能大于结束日期')

        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        start_time, end_time = utils.get_range_start_end_time(start_day, end_day, store['st'], store['ed'])

        revenue = ctrl.trade.get_day_revenues_ctl(store_id, start_time, end_time)

        self.send_json({
            'revenue': revenue
        })

    @erp_auth
    def get(self):
        '''
        营业收入分析
        '''
        try:
            day = self.get_argument('day', 'today')
            start_day = self.get_argument('start_day', '')
            end_day = self.get_argument('end_day', '')

            assert(day in ['today', 'yesterday', '7days', '30days'])
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']

        if self.has_argument('day'):
            self.get_day_revenues(store_id, day)
        else:
            self.get_query_revenues(store_id, start_day, end_day)


class StatProductHandler(BaseHandler):

    def get_day_product_sales(self, store_id, day, order_by, page=1, page_size=10):
        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        st = store['st']
        ed = store['ed']

        if day == 'today':
            start_time, end_time = utils.get_today_start_end_time(st, ed)
        elif day == 'yesterday':
            start_time, end_time = utils.get_yesterday_start_end_time(st, ed)
        elif day == '7days':
            start_time, end_time = utils.get_7days_start_end_time(st, ed)
        else:
            start_time, end_time = utils.get_30days_start_end_time(st, ed)

        sales, count = ctrl.trade.get_day_product_sales_ctl(store_id, start_time, end_time, order_by, page, page_size)
        total_page = (count + page_size - 1) // page_size

        self.send_json({
            'list': sales,
            'page': page,
            'total_page': total_page,
            'total_count': count
        })

    def get_query_product_sales(self, store_id, start_day, end_day, order_by, page=1, page_size=10):
        try:
            start_day = arrow.get(start_day, 'YYYY-MM-DD')
            end_day = arrow.get(end_day, 'YYYY-MM-DD')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001, errmsg='日期格式不合法')

        if start_day > end_day:
            raise utils.APIError(errcode=10001, errmsg='起始日期不能大于结束日期')

        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        start_time, end_time = utils.get_range_start_end_time(start_day, end_day, store['st'], store['ed'])

        sales, count = ctrl.trade.get_day_product_sales_ctl(store_id, start_time, end_time, order_by, page, page_size)
        total_page = (count + page_size - 1) // page_size

        self.send_json({
            'list': sales,
            'page': page,
            'total_page': total_page,
            'total_count': count
        })

    @erp_auth
    def get(self):
        '''
        酒水销售统计分析
        '''
        try:
            day = self.get_argument('day', 'today')
            start_day = self.get_argument('start_day', '')
            end_day = self.get_argument('end_day', '')
            order_by = self.get_argument('order_by', 'count')
            page = int(self.get_argument('page', 1))
            page_size = int(self.get_argument('page_size', 10))

            assert(day in ['today', 'yesterday', '7days', '30days'])
            assert(order_by in ['count', 'money'])
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']

        if self.has_argument('day'):
            self.get_day_product_sales(store_id, day, order_by, page, page_size)
        else:
            self.get_query_product_sales(store_id, start_day, end_day, order_by, page, page_size)


class StatPackHandler(BaseHandler):

    def get_day_pack_sales(self, store_id, day, order_by, page=1, page_size=10):
        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        st = store['st']
        ed = store['ed']

        if day == 'today':
            start_time, end_time = utils.get_today_start_end_time(st, ed)
        elif day == 'yesterday':
            start_time, end_time = utils.get_yesterday_start_end_time(st, ed)
        elif day == '7days':
            start_time, end_time = utils.get_7days_start_end_time(st, ed)
        else:
            start_time, end_time = utils.get_30days_start_end_time(st, ed)

        sales, count = ctrl.trade.get_day_pack_sales_ctl(store_id, start_time, end_time, order_by, page, page_size)
        total_page = (count + page_size - 1) // page_size
        self.send_json({
            'list': sales,
            'page': page,
            'total_page': total_page,
            'total_count': count
        })

    def get_query_pack_sales(self, store_id, start_day, end_day, order_by, page=1, page_size=10):
        try:
            start_day = arrow.get(start_day, 'YYYY-MM-DD')
            end_day = arrow.get(end_day, 'YYYY-MM-DD')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001, errmsg='日期格式不合法')

        if start_day > end_day:
            raise utils.APIError(errcode=10001, errmsg='起始日期不能大于结束日期')

        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        start_time, end_time = utils.get_range_start_end_time(start_day, end_day, store['st'], store['ed'])

        sales, count = ctrl.trade.get_day_pack_sales_ctl(store_id, start_time, end_time, order_by, page, page_size)
        total_page = (count + page_size - 1) // page_size

        self.send_json({
            'list': sales,
            'page': page,
            'total_page': total_page,
            'total_count': count
        })

    @erp_auth
    def get(self):
        '''
        酒水销售统计分析
        '''
        try:
            day = self.get_argument('day', 'today')
            start_day = self.get_argument('start_day', '')
            end_day = self.get_argument('end_day', '')
            order_by = self.get_argument('order_by', 'count')
            page = int(self.get_argument('page', 1))
            page_size = int(self.get_argument('page_size', 10))

            assert(day in ['today', 'yesterday', '7days', '30days'])
            assert(order_by in ['count', 'money'])
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']

        if self.has_argument('day'):
            self.get_day_pack_sales(store_id, day, order_by, page, page_size)
        else:
            self.get_query_pack_sales(store_id, start_day, end_day, order_by, page, page_size)


class OrderHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        账单查询
        '''
        try:
            day = self.get_argument('day', 'today')
            start_day = self.get_argument('start_day', '')
            end_day = self.get_argument('end_day', '')
            page = int(self.get_argument('page', 1))
            room_id = int(self.get_argument('room_id', 0))
            page_size = int(self.get_argument('page_size', 10))
            export = int(self.get_argument('export', 0))

            assert(day in ['today', 'yesterday', '7days', '30days'])
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']

        if self.has_argument('day'):
            start_time, end_time = self.get_day_orders(store_id, room_id, day)
        else:
            start_time, end_time = self.get_query_orders(store_id, room_id, start_day, end_day)

        if not export:
            summary = ctrl.trade.get_day_orders_summary_ctl(store_id, start_time, end_time, room_id, page, page_size)
            return self.send_json({
                'detail': summary
            })

        orders = ctrl.trade.get_query_orders(store_id, start_time, end_time, room_id, is_total=True)
        [order.update({'room_name': ctrl.room.get_room_ctl(order.get('room_id'))['name']}) for order in orders]
        url = self.save_xlsx_data(orders, store_id)
        self.send_json({
            'url': url
        })

    def save_xlsx_data(self, orders, store_id):
        filename = 'static/data/订单流水%s.xlsx' % store_id
        sheet_dict = {
            'sheetname': '订单流水%s.xlsx'%store_id,
            'titles': ['序号', '账单号', '房号', '总计', '实收', '结账时间']
        }
        [sheet_dict.setdefault('data', []).append([idx+1, o['order_no'], o['room_name'], '%.02f'%(o['money']/100), '%.02f'%(o['real_money']), o['finish_time']])
            for idx, o in enumerate(orders)]

        filename_with_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        sheet = [sheet_dict]
        utils.export_xlsx(data=sheet, export_filename=filename_with_path)
        return self.request.protocol + '://' + self.request.host + '/' + filename

    def get_day_orders(self, store_id, room_id, day):
        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        st = store['st']
        ed = store['ed']

        if day == 'today':
            start_time, end_time = utils.get_today_start_end_time(st, ed)
        elif day == 'yesterday':
            start_time, end_time = utils.get_yesterday_start_end_time(st, ed)
        elif day == '7days':
            start_time, end_time = utils.get_7days_start_end_time(st, ed)
        else:
            start_time, end_time = utils.get_30days_start_end_time(st, ed)

        return start_time, end_time

    def get_query_orders(self, store_id, room_id, start_day, end_day):
        try:
            start_day = arrow.get(start_day, 'YYYY-MM-DD')
            end_day = arrow.get(end_day, 'YYYY-MM-DD')
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001, errmsg='日期格式不合法')

        if start_day > end_day:
            raise utils.APIError(errcode=10001, errmsg='起始日期不能大于结束日期')

        store = ctrl.store.get_store_ctl(self.current_user['phone'])
        start_time, end_time = utils.get_range_start_end_time(start_day, end_day, store['st'], store['ed'])

        return start_time, end_time


class OrderBillHandler(BaseHandler):

    @erp_auth
    def get(self):
        '''
        获取账单明细
        '''
        try:
            order_id = int(self.get_argument('order_id'))
            order_no = int(self.get_argument('order_no'))
        except Exception as e:
            logging.error(e)
            raise utils.APIError(errcode=10001)

        store_id = self.current_user['store_id']

        order = ctrl.order.get_order_ctl(store_id, order_no)

        data = {
            'detail': {}
        }

        if not order:
            return self.send_json(data)

        bills = ctrl.order.get_order_bills_ctl(store_id, order_id)

        order['list'] = bills
        data['detail'] = order

        self.send_json(data)

