"""Homeflux Data Types"""
import abc
import datetime
from typing import Optional

from pydantic import BaseModel

from homeflux import environment, log


class AbstractRecord(BaseModel, metaclass=abc.ABCMeta):
    """Abstract base record with base functionality.

    """
    _bucket: str = 'home'
    timescale: str
    time: datetime.datetime

    @property
    def bucket(self) -> str:
        """Return the full bucket name of {self.bucket_name}-{self.timescale}.

        Returns:
            str: Full bucket name.
        """
        return f'{self._bucket}-{self.timescale}'

    @abc.abstractmethod
    def as_influx_dict(self) -> dict:
        """Return the data for this instance as a dict to be inserted into InfluxDB.

        Returns:
            dict: Instance data as a dict to insert into InfluxDB.
        """
        pass


class PowerRecord(AbstractRecord):
    raw_value: float
    unit: str
    source: str
    location: str
    tags: Optional[dict]

    def __repr__(self) -> str:
        return f'[{self.__class__.__name__} {self.source} {self.location} {str(self.time)} {self.value}Wh]'

    @property
    def value(self) -> float:
        """Value property to convert units to Watt Hours.

        Returns:
            float: Power in Watt Hours.
        """
        if self.unit.upper() == 'KWH':
            return self.raw_value * 1000.0
        elif self.unit.upper() == 'WH':
            return self.raw_value
        else:
            if not environment.TEST:
                log.error('Invalid unit type: %s', self.unit)
            return 0.0

    def as_influx_dict(self) -> dict:
        tags = {'data_source': 'homeflux', 'source': self.source}
        if self.tags:
            tags.update(self.tags)

        return {'measurement': 'power',
                'tags': tags,
                'time': self.time,
                'fields': {'power_usage': self.value}
                }


class ClimateRecord(AbstractRecord):
    raw_value: float
    location: str
    source: str

    def __repr__(self) -> str:
        return f'[{self.__class__.__name__} {self.time} {self.value}°F]'

    @property
    def value(self) -> float:
        return float(self.raw_value)

    def as_influx_dict(self) -> dict:
        return {'measurement': 'temperature',
                'tags': {'data_source': 'homeflux',
                         'location': self.location,
                         'source': self.source},
                'time': self.time,
                'fields': {'temperature': self.value}
                }
