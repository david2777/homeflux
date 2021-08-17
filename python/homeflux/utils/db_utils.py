"""Module for various InfluxDB Utilities"""

from influxdb_client import InfluxDBClient

from homeflux import log, environment


def seed_buckets(delete_existing=False):
    _buckets = ['home']
    _times = ['minute', 'hour', 'day', 'week']
    buckets = [f'{b}-{t}' for b in _buckets for t in _times]

    client = InfluxDBClient(url=environment.INFLUX_URL, token=environment.INFLUX_TOKEN, org=environment.INFLUX_ORG)
    api = client.buckets_api()
    for bucket in buckets:
        search = api.find_bucket_by_name(bucket)
        if search:
            if delete_existing:
                log.info('Deleting bucket %s on %s', bucket, environment.INFLUX_URL)
                api.delete_bucket(search)
            else:
                log.info('Bucket %s on %s already exists', bucket, environment.INFLUX_URL)
                continue

        log.info('Creating bucket %s on %s', bucket, environment.INFLUX_URL)
        api.create_bucket(bucket_name=bucket, org=environment.INFLUX_ORG)

