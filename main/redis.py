
from django.conf import settings
from redis.client import StrictRedis
from redlock import Redlock


def get_redis_client():
    redis_client = StrictRedis.from_url(settings.REDIS_URL)
    return redis_client

def get_redlock_client():
    redlock_client = Redlock([settings.REDIS_URL], 1)
    return redlock_client