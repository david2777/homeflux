"""Module for interacting with the InfluxDB database"""
from typing import List

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from homeflux.utils import timer
from homeflux import environment, log
from homeflux.data import data_types


def write(values: List[data_types.AbstractRecord]) -> None:
    """Write the list of records to the database.

    Args:
        values (List[data_types.AbstractRecord]): List of records to insert into the database.

    Returns:
        None
    """
    # Open connection to database
    t = timer.Timer()
    client = InfluxDBClient(url=environment.INFLUX_URL, token=environment.INFLUX_TOKEN, org=environment.INFLUX_ORG)
    log.debug('Writing %s points to %s', len(values), environment.INFLUX_URL)
    with client.write_api(write_options=SYNCHRONOUS) as api:
        # Group items by bucket
        out_dict = {}
        for obj in values:
            if obj.bucket not in out_dict:
                out_dict[obj.bucket] = []
            out_dict[obj.bucket].append(obj.as_influx_dict())

        # Insert data into database
        for bucket, data_list in out_dict.items():
            log.info('Writing %s points to bucket: %s', len(data_list), bucket)
            for data_to_write in data_list:
                api.write(bucket, environment.INFLUX_ORG, data_to_write)

    log.info('Took %s seconds to write %s points %s', t.end(), len(values), environment.INFLUX_URL)
