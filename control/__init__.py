#!/usr/bin/env python
# -*- coding: utf-8 -*-

from control.cache import _redis
from control.store import StoreCtrl
from control.room import RoomCtrl
from control.pack import PackCtrl
from control.cate import CateCtrl
from control.order import OrderCtrl
from control.calc import CalcCtrl
from control.open import OpenCtrl
from control.trade import TradeCtrl
from mysql import pdb

class Ctrl(object):

    def __init__(self):
        self.__method_ren()

        self.pdb = pdb
        self.rs = _redis

        self.store = StoreCtrl(self)
        self.room = RoomCtrl(self)
        self.pack = PackCtrl(self)
        self.cate = CateCtrl(self)
        self.order = OrderCtrl(self)
        self.calc = CalcCtrl(self)
        self.open = OpenCtrl(self)
        self.trade = TradeCtrl(self)

    def __method_ren(self):
        '''
        重命名control下的函数名，防止命名冲突
        '''
        for std in globals():
            if std.find('Ctrl') == -1:
                continue

            cls = globals()[std]
            for func in dir(cls):
                if callable(getattr(cls, func)) and not func.startswith('__'):
                    setattr(cls, '%s_ctl' % func, getattr(cls, func))
                    delattr(cls, func)

# global, called by handler
ctrl = Ctrl()
