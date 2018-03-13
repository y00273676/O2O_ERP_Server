#!/usr/bin/env python
# -*- coding: utf-8 -*-

# redis
REDIS = {
    'host': '10.9.36.222',
    'port': 6379
}

# mysql
DB_ERP = 'erp'
DB_ERP_ORDER = 'erp_order'
MYSQL_ERP = {
    DB_ERP: {
        'master': {
            'host': '10.9.115.163',
            'user': 'root',
            'pass': '098f6bcd4621d373cade4e832627b4f6',
            'port': 3306
        },
        'slaves': [
            {
                'host': '10.9.156.178',
                'user': 'root',
                'pass': '098f6bcd4621d373cade4e832627b4f6',
                'port': 3306
            }
        ]
    },
    DB_ERP_ORDER: {
        'master': {
            'host': '10.9.115.163',
            'user': 'root',
            'pass': '098f6bcd4621d373cade4e832627b4f6',
            'port': 3306
        },
        'slaves': [
            {
                'host': '10.9.156.178',
                'user': 'root',
                'pass': '098f6bcd4621d373cade4e832627b4f6',
                'port': 3306
            }
        ]
    }
}

ERR_MSG = {
    200: '服务正常',

    10001: '请求参数错误',
    10002: '用户未登录',
    10003: '支付失败，请重新支付',

    50001: '系统错误',
    50002: '非法请求'
}

# time
A_MINUTE = 60
A_HOUR = 3600
A_DAY = 24 * A_HOUR

# state
STATE = {
    'unvalid': 0,   # 下架
    'valid': 1,     # 上架
    'delete': 2     # 删除
}

# 包房状态
ROOM_TYPE = {
    'free': 1,      # 空闲
    'using': 2,     # 使用中
    'timeout': 3,   # 超时
    'clean': 4,     # 清扫
    'fault': 5      # 故障
}

# 支付方式
PAY_MD = {
    'cash': 1,
    'wechat': 2,
    'alipay': 3,
    'pos': 4,
    'member': 5
}

# 支付状态
PAY_TYPE = {
    'current': 1,   # 现结
    'poster': 2     # 落单后结
}

# 订单支付状态
BILL_PAY_STATE = {
    'unpay': 0,     # 未付
    'pay': 1,       # 已付
    'cancel': 2     # 取消
}

# 开房状态
ORDER_STATE = {
    'using': 1,     # 进行中
    'finish': 2,    # 已完结
    'invalid': 3    # 已作废
}

# 账单类型
BILL_MD = {
    'time': 1,      # 计时
    'pack': 2       # 套餐
}

# 酒水账单类型
BILL_PRO_MD = {
    'product': 1,   # 单品
    'pack': 2       # 套餐
}

# 业务类型
SERVICE_TYPE = {
    'room': 1,      # 房费
    'product': 2,   # 酒水
    'prepay': 3,    # 预付
    'back': 4       # 退单
}

VERIFY_SMS_CONTENT = '【互联网KTV】验证码：{code}（5分钟内有效），请您尽快完成系统注册。'

COMMON_URL = 'http://gm.ktvsky.3231266f50027675yg.custom.ucloud.cn'

# try to load debug settings
try:
    from tornado.options import options
    if options.debug:
        exec(compile(open('settings.debug.py')
             .read(), 'settings.debug.py', 'exec'))
except:
    pass
