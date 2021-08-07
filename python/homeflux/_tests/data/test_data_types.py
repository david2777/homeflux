"""Tests for homeflux.data.data_types"""
from datetime import datetime
import unittest

from homeflux.data import data_types


class TestPowerRecord(unittest.TestCase):
    def test_as_influxdb(self):
        r = data_types.PowerRecord(raw_value=1.25, unit='WH', source='test_source', location='test_location',
                                   time=datetime(2021, 4, 20, 00, 00, 00), timescale='hour', tags={'test': 'test'})

        e = {'measurement': 'power', 'tags': {'data_source': 'homeflux', 'source': 'test_source', 'test': 'test'},
             'time': datetime(2021, 4, 20, 00, 00, 00), 'fields': {'power_usage': 1.25}}

        self.assertDictEqual(r.as_influx_dict(), e)

    def test_bucket(self):
        data = {'raw_value': 2.5, 'source': 'test_source', 'location': 'test_location', 'time': datetime.now(),
                'unit': 'KW'}
        r = data_types.PowerRecord(**data, timescale='hour')
        self.assertEqual('home-hour', r.bucket)

    def test_unit_conversions(self):
        data = {'raw_value': 2.5, 'source': 'test_source', 'location': 'test_location', 'timescale': 'hour',
                'time': datetime.now()}
        wh = data_types.PowerRecord(unit='WH', **data)
        kwh = data_types.PowerRecord(unit='KWH', **data)
        broken = data_types.PowerRecord(unit='gigawatts', **data)
        self.assertIsInstance(wh.value, float)
        self.assertIsInstance(kwh.value, float)
        self.assertIsInstance(broken.value, float)
        self.assertEqual(2.5, wh.value)
        self.assertEqual(2500.0, kwh.value)
        self.assertEqual(0.0, broken.value)


class TestClimateRecord(unittest.TestCase):
    def test_as_influxdb(self):
        r = data_types.ClimateRecord(timescale='hour', time=datetime(2021, 4, 20, 00, 00, 00),
                                     raw_value=79.9, location='test_location', source='test_source')
        e = {'measurement': 'temperature', 'time': datetime(2021, 4, 20, 00, 00, 00), 'fields': {'temperature': 79.9},
             'tags': {'data_source': 'homeflux', 'location': 'test_location', 'source': 'test_source'}}
        self.assertDictEqual(e, r.as_influx_dict())

    def test_bucket(self):
        r = data_types.ClimateRecord(timescale='minute', time=datetime(2021, 4, 20, 00, 00, 00),
                                     raw_value=79.9, location='test_location', source='test_source')
        self.assertEqual('home-minute', r.bucket)


if __name__ == '__main__':
    unittest.main()
