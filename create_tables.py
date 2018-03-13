# coding:utf-8
import os
import logging

from tornado.options import options, define
define('debug', default=True, help='enable debug mode')
options.parse_command_line()

from control import ctrl
from lib.decorator import try_script_error
from settings import MYSQL_ERP, DB_ERP_ORDER

erp_order = MYSQL_ERP['erp_order']['master']

ORDER_TABLE = '''
    CREATE TABLE if not exists `t_order_%s` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `order_no` varchar(16) NOT NULL DEFAULT '' COMMENT '订单编号',
        `room_id` int(11) NOT NULL DEFAULT '0' COMMENT '包房ID',
        `st` char(16) NOT NULL DEFAULT '' COMMENT '开台时间，如：2017.01.01 08:00',
        `ed` char(16) NOT NULL DEFAULT '' COMMENT '关台时间，如：2017.01.01 10:00',
        `minute` int(11) NOT NULL DEFAULT '0' COMMENT '使用时长',
        `prepay` int(11) NOT NULL DEFAULT '0' COMMENT '预付金额，单位：分',
        `money` int(11) NOT NULL DEFAULT '0' COMMENT '应收金额，单位：分',
        `real_money` int(11) NOT NULL DEFAULT '0' COMMENT '实收金额，单位：分',
        `pay_type` tinyint(1) NOT NULL DEFAULT '1' COMMENT '支付状态：1现结/2落单后结',
        `describe` varchar(512) NOT NULL DEFAULT '' COMMENT '备注',
        `state` tinyint(1) NOT NULL DEFAULT '1' COMMENT '状态：1进行中/2已完结/3已作废',
        `finish_time` datetime DEFAULT NULL COMMENT '结账时间',
        `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `pay_id` varchar(128) NOT NULL DEFAULT '',
        PRIMARY KEY (`id`),
        KEY `idx_rid_state` (`room_id`,`state`),
        KEY `idx_order_no` (`order_no`),
        KEY `idx_state_finishtime_roomid` (`state`, `finish_time`, `room_id`)
    ) ENGINE=InnoDB CHARSET=utf8;
'''

BILL_TABLE = '''
    CREATE TABLE if not exists `t_bill_%s` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `order_id` int(11) NOT NULL DEFAULT '0' COMMENT '订单ID',
        `bill_no` varchar(18) NOT NULL DEFAULT '' COMMENT '流水号',
        `room_id` int(11) NOT NULL DEFAULT '0' COMMENT '包房ID',
        `money` int(11) NOT NULL DEFAULT '0' COMMENT '应收金额，单位：分',
        `real_money` int(11) NOT NULL DEFAULT '0' COMMENT '实收金额，单位：分',
        `rate` int(11) NOT NULL DEFAULT '100' COMMENT '打折，折扣率0-100',
        `pay_md` tinyint(1) NOT NULL DEFAULT '1' COMMENT '支付方式：1现金/2微信/3支付宝/4POS支付/5会员卡支付',
        `pay_state` tinyint(1) NOT NULL DEFAULT '0' COMMENT '支付状态：0未付/1已付/2取消',
        `service_type` tinyint(1) NOT NULL DEFAULT '1' COMMENT '业务类型：1房费/2酒水/3预付/4退单',
        `describe` varchar(512) NOT NULL DEFAULT '' COMMENT '备注',
        `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `pay_id` varchar(128) NOT NULL DEFAULT '',
        `extra` varchar(128) NOT NULL DEFAULT '{}',
        PRIMARY KEY (`id`),
        KEY `idx_order_id` (`order_id`),
        KEY `idx_paystate_servicetype_updatetime` (`pay_state`, `service_type`, `update_time`)
    ) ENGINE=InnoDB CHARSET=utf8;
'''

BILL_ROOM_TABLE = '''
    CREATE TABLE if not exists `t_bill_room_%s` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `order_id` int(11) NOT NULL DEFAULT '0' COMMENT '订单ID',
        `bill_id` int(11) NOT NULL DEFAULT '0' COMMENT '账单ID',
        `room_id` int(11) NOT NULL DEFAULT '0' COMMENT '包房ID',
        `fee_id` int(11) NOT NULL DEFAULT '0' COMMENT '计费方式ID',
        `pack_id` int(11) NOT NULL DEFAULT '0' COMMENT '套餐ID',
        `st` char(16) NOT NULL DEFAULT '' COMMENT '开始时间，如：2017.01.01 08:00',
        `ed` char(16) NOT NULL DEFAULT '' COMMENT '结束时间，如：2017.01.01 10:00',
        `minute` int(11) NOT NULL DEFAULT '0' COMMENT '消费时长',
        `money` int(11) NOT NULL DEFAULT '0' COMMENT '金额，单位：分',
        `md` tinyint(1) NOT NULL DEFAULT '1' COMMENT '计费方式：1计时/2套餐',
        `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        KEY `idx_order_id` (`order_id`)
    ) ENGINE=InnoDB CHARSET=utf8;
'''

BILL_PRODUCT_TABLE = '''
    CREATE TABLE if not exists `t_bill_product_%s` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
        `order_id` int(11) NOT NULL DEFAULT '0' COMMENT '订单ID',
        `bill_id` int(11) NOT NULL DEFAULT '0' COMMENT '账单ID',
        `room_id` int(11) NOT NULL DEFAULT '0' COMMENT '包房ID',
        `product_id` int(11) NOT NULL DEFAULT '0' COMMENT '商品ID',
        `pack_id` int(11) NOT NULL DEFAULT '0' COMMENT '套餐ID',
        `count` int(11) NOT NULL DEFAULT '0' COMMENT '数量',
        `unit` varchar(16) NOT NULL DEFAULT '' COMMENT '单位',
        `money` int(11) NOT NULL DEFAULT '0' COMMENT '金额，单位：分',
        `md` tinyint(1) NOT NULL DEFAULT '1' COMMENT '酒水类型：1单品/2套餐',
        `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        KEY `idx_order_id` (`order_id`),
        KEY `idx_billid_productid` (`bill_id`, `product_id`),
        KEY `idx_billid_packid` (`bill_id`, `pack_id`)
    ) ENGINE=InnoDB CHARSET=utf8;
'''

tables = [ORDER_TABLE, BILL_TABLE, BILL_ROOM_TABLE, BILL_PRODUCT_TABLE]
sqlfile = 'erp_order_tables.sql'
sql = 'mysql -u{user} -p{passwd} -h{host} -P{port} {db} < {sql_file}'.format(
    user=erp_order['user'],
    passwd=erp_order['pass'],
    host=erp_order['host'],
    port=erp_order['port'],
    db=DB_ERP_ORDER,
    sql_file=sqlfile)
logging.error(sql)

def get_newly_generated_store_id():
    stores = ctrl.store.get_latest_stores()
    return [i['store_id'] for i in stores]

@try_script_error
def main():
    store_ids = get_newly_generated_store_id()
    if not store_ids:
        return

    tables_to_create = []
    for _id in store_ids:
        for t in tables:
            sql_str = t % _id
            tables_to_create.append(sql_str)

    with open(sqlfile, 'w') as f:
        f.writelines(tables_to_create)

    os.system(sql)


if __name__ == "__main__":
    main()
