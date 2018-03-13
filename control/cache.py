#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis

from settings import REDIS

def get_redis_client():
    print('redis: %s' % REDIS['host'])
    return redis.StrictRedis(host=REDIS['host'], port=REDIS['port'])

_redis = get_redis_client()

