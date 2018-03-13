#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from decimal import Decimal
from datetime import datetime, date

def datetime_str(handler, time_obj):
    return time_obj.strftime('%Y-%m-%d %H:%M:%S')

def json_format(handler, res):

    def _format(obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, Decimal):
            return ('%.2f' % obj)
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')

    return json.dumps(res, default=_format)

def date_time_to_date(handler, date_time):
    return datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S').date()
