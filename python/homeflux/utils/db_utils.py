"""Module for various InfluxDB Utilities"""
import datetime

from influxdb_client import InfluxDBClient

from homeflux import log, environment
from homeflux.data import database as db
from homeflux.agents import gwp_opower


def generate_buckets(delete_existing: bool = False):
    """Generate the default buckets on the InfluxDB server.

    Args:
        delete_existing (bool): If True, will delete the buckets if they already exist.

    Returns:
        None
    """
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


async def seed_opower_historical():
    """Seed the database with historical data going back to when the meter was started.

    Returns:
        None
    """
    online_date = datetime.date(2019, 5, 2)
    current_date = datetime.date.today()
    delta = int((current_date - online_date).days)

    meter = gwp_opower.Meter(environment.GWP_USER, environment.GWP_PASSWORD, environment.GWP_UUID)

    start = -31
    end = -1
    async with meter:
        while abs(start) < delta:
            log.info('Pulling historical data %s => %s', current_date - datetime.timedelta(abs(start)),
                     current_date - datetime.timedelta(abs(end)))
            power_hourly = await meter.get_power_hourly(start, end)
            weather_hourly = await meter.get_weather_hourly(start, end)
            power_daily = await meter.get_power_daily(start, end)
            weather_daily = await meter.get_weather_daily(start, end)
            db.write(values=power_hourly)
            db.write(values=weather_hourly)
            db.write(values=power_daily)
            db.write(values=weather_daily)
            start -= 30
            end -= 30
