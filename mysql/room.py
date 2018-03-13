#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TINYINT, CHAR, ENUM

from settings import DB_ERP, STATE
from mysql.base import NotNullColumn, Base
from lib.decorator import model_to_dict, models_to_list, filter_update_data


class TRoomType(Base):
    '''
    房型表
    '''
    __tablename__ = 't_room_type'

    store_id = Column(INTEGER(11))
    name = NotNullColumn(VARCHAR(128))
    pic = NotNullColumn(VARCHAR(128))
    min_man = Column(TINYINT(2), server_default='0')
    max_man = Column(TINYINT(2), server_default='0')
    state = Column(TINYINT(1), server_default='1')  # 状态：1有效/2删除


class TRoom(Base):
    '''
    包房表
    '''
    __tablename__ = 't_room'

    store_id = Column(INTEGER(11))
    rt_id = Column(INTEGER(11), server_default='0')
    name = NotNullColumn(VARCHAR(128))
    ip = NotNullColumn(VARCHAR(128))
    mac = NotNullColumn(VARCHAR(128))
    room_type = Column(TINYINT(1), server_default='1')         # 包房状态：1空闲/2使用/3超时/4清扫/5故障
    describe = NotNullColumn(VARCHAR(512))                     # 备注
    state = Column(TINYINT(1), server_default='1')             # 状态：1有效/2删除


class TRoomFee(Base):
    '''
    计费表
    '''
    __tablename__ = 't_room_fee'

    store_id = Column(INTEGER(11))
    rt_id = Column(INTEGER(11), server_default='0')
    st = Column(CHAR(5), server_default='')
    ed = Column(CHAR(5), server_default='')
    fee = Column(INTEGER(11), server_default='0')
    day_or_holiday = Column(VARCHAR(10), server_default='')    # 周几1-7/节假日
    md = Column(ENUM('day', 'holiday'), server_default='day')  # 类型：周几/节假日
    state = Column(TINYINT(1), server_default='1')             # 状态：1有效/2删除


class TRoomPack(Base):
    '''
    包房套餐表
    '''
    __tablename__ = 't_room_pack'

    store_id = Column(INTEGER(11))
    rt_id = Column(INTEGER(11), server_default='0')
    pack_id = Column(INTEGER(11), server_default='0')
    state = Column(TINYINT(1), server_default='1')             # 状态：1有效/2删除


class RoomModel(object):

    def __init__(self, pdb):
        self.pdb = pdb
        self.master = pdb.get_session(DB_ERP, master=True)
        self.slave = pdb.get_session(DB_ERP)

    @models_to_list
    def add_room_types(self, store_id, names):
        room_types = []
        for name in names:
            room = TRoomType(store_id=store_id, name=name)
            self.master.add(room)
            room_types.append(room)
        self.master.commit()
        return room_types

    def delete_room_type(self, store_id, rt_id):
        q = self.master.query(TRoomType).filter_by(id=rt_id, store_id=store_id)
        q.update({
            'state': STATE['delete']
        })
        self.master.commit()

    @filter_update_data
    def update_room_type(self, rt_id, store_id, data={}):
        q = self.master.query(TRoomType).filter_by(id=rt_id, store_id=store_id)
        q.update(data)
        self.master.commit()

    @models_to_list
    def get_room_types(self, store_id):
        q = self.slave.query(TRoomType)
        q = q.filter_by(store_id=store_id, state=STATE['valid'])
        return q.all()

    @models_to_list
    def add_rooms(self, store_id, rooms):
        room_list = []
        for rt_id in rooms.keys():
            ip_names = rooms[rt_id]
            for ip_name in ip_names:
                room = TRoom(store_id=store_id, rt_id=rt_id, name=ip_name['name'], ip=ip_name.get('ip', ''), mac=ip_name.get('mac', ''))
                room_list.append(room)
                self.master.add(room)
        self.master.commit()
        return room_list

    @model_to_dict
    def delete_room(self, room_id, store_id):
        q = self.master.query(TRoom).filter_by(id=room_id, store_id=store_id)
        room = q.scalar()
        q.update({
            'state': STATE['delete']
        })
        self.master.commit()
        return room

    @model_to_dict
    @filter_update_data
    def update_room(self, room_id, store_id, data={}):
        q = self.master.query(TRoom).filter_by(id=room_id, store_id=store_id)
        room = q.scalar()
        q.update(data)
        self.master.commit()
        return room

    @models_to_list
    def get_rooms(self, room_ids):
        q = self.slave.query(TRoom)
        q = q.filter(TRoom.id.in_(tuple(room_ids)))
        # q = q.filter(TRoom.id.in_(tuple(room_ids))).filter_by(state=STATE['valid'])
        return q.all()

    def get_rt_room_ids(self, store_id, rt_id):
        q = self.slave.query(TRoom.id).filter_by(store_id=store_id, rt_id=rt_id, state=STATE['valid'])
        rooms = q.all()
        return [int(room.id) for room in rooms]

    def get_store_room_ids(self, store_id):
        q = self.slave.query(TRoom.id).filter_by(store_id=store_id, state=STATE['valid'])
        rooms = q.all()
        return [int(room.id) for room in rooms]

    @models_to_list
    def add_room_fees(self, store_id, rt_id, fees):
        fee_list = []
        for fee in fees:
            day = fee.get('day', '')
            holiday = fee.get('holiday', '')
            day_or_holiday = day or holiday
            items = fee['list']
            for item in items:
                fee = TRoomFee(store_id=store_id, rt_id=rt_id, st=item['st'], ed=item['ed'], fee=item['fee'], day_or_holiday=day_or_holiday, md='day' if day else 'holiday')
                fee_list.append(fee)
                self.master.add(fee)
        self.master.commit()
        return fee_list

    @models_to_list
    def get_room_fees(self, store_id, rt_id, day_or_holiday, md='day'):
        q = self.slave.query(TRoomFee).filter_by(store_id=store_id, rt_id=rt_id, md=md, state=STATE['valid'])
        if day_or_holiday:
            q = q.filter_by(day_or_holiday=day_or_holiday)
        return q.all()

    def delete_room_fees(self, store_id, rt_id, day_or_holiday, md='day'):
        q = self.master.query(TRoomFee).filter_by(store_id=store_id, rt_id=rt_id, md=md)
        if day_or_holiday:
            q = q.filter_by(day_or_holiday=day_or_holiday)

        data = {
            'state': STATE['delete']
        }
        q.update(data, synchronize_session=False)
        self.master.commit()

    @model_to_dict
    def delete_room_fee(self, store_id, fee_id):
        q = self.master.query(TRoomFee).filter_by(id=fee_id, store_id=store_id)
        fee = q.scalar()
        q.update({
            'state': STATE['delete']
        })
        self.master.commit()
        return fee

    @model_to_dict
    @filter_update_data
    def update_room_fee(self, fee_id, store_id, data={}):
        q = self.master.query(TRoomFee).filter_by(id=fee_id, store_id=store_id)
        fee = q.scalar()
        q.update(data)
        self.master.commit()
        return fee

    def add_room_pack(self, store_id, rt_id, pack_id):
        room_pack = TRoomPack(store_id=store_id, rt_id=rt_id, pack_id=pack_id)
        self.master.add(room_pack)
        self.master.commit()

    def get_room_pack_ids(self, store_id, rt_id):
        q = self.slave.query(TRoomPack.pack_id).filter_by(store_id=store_id, rt_id=rt_id, state=STATE['valid'])
        packs = q.all()
        return [int(pack.pack_id) for pack in packs]

    def delete_room_pack(self, store_id, pack_id):
        q = self.master.query(TRoomPack).filter_by(store_id=store_id, pack_id=pack_id)
        q.update({
            'state': STATE['delete']
        })
        self.master.commit()

