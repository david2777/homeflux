"""Module for interacting with NUT (Network UPS Tools)"""
import datetime
from typing import Union, Optional

import nut2
from nut2 import PyNUTClient

from homeflux import environment, log
from homeflux.data.data_types import PowerRecord


class NutError(RuntimeError):
    pass


class NutClient(object):
    """Class for querying a NUT (Network UPS Tools) server.

    """
    host_name: str
    ip_address: str
    timescale: str
    port: int
    nut_client: Union[PyNUTClient, None] = None

    def __init__(self, host_name: str, ip_address: str, timescale: str, port: int = None):
        """Initialize Client Object (without connecting).

        Args:
            host_name (str): Host name (used for recording tag to InfluxDB)
            ip_address (str): IP Address of the server, used to connect to the server.
            timescale (str): Timescale, used to determine which bucket the data goes into.
            port (Optional[int]): Optional explicit port, default from environment.
        """
        self.host_name = host_name
        self.ip_address = ip_address
        self.timescale = timescale
        self.port = port if port is not None else environment.NUT_PORT

    def __repr__(self):
        return f'[{self.__class__.__name__} {self.host_name} {self.ip_address}@{self.port}]'

    async def __aenter__(self):
        await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Connect to the NUT client and instantiate the self.nut_client instance.

        """
        try:
            log.info('Connecting to NUT Server %s@%s', self.ip_address, self.port)
            self.nut_client = PyNUTClient(host=self.ip_address, port=self.port, login=environment.NUT_USERNAME,
                                          password=environment.NUT_PASSWORD, debug=False)
        except nut2.PyNUTError:
            raise NutError(f'Failed to connect to {self.ip_address}')

    async def disconnect(self):
        """Disconnect from the NUT client by deleting the self.nut_client instance.

        """
        log.debug('Disconnecting from NUT Server')
        del self.nut_client
        self.nut_client = None

    async def read(self) -> PowerRecord:
        """Return a reading from the NUT server in form of a PowerRecord object.

        Returns:
            PowerRecord: PowerRecord object for this reading.
        """
        dc = False
        if self.nut_client is None:
            await self.connect()
            dc = True

        raw_data = self.nut_client.list_vars(environment.NUT_UPS_NAME)

        try:
            load = float(raw_data['ups.load'])
            if not load:
                log.debug('UPS has no load')
                value = 0.0
            else:
                log.debug('Load is %s', load)
                value = round(float(raw_data['ups.realpower.nominal']) * 0.01 * load, 1)
                log.debug('Power usage is %s', value)
            dt = datetime.datetime.utcnow().replace(microsecond=0)
            r = PowerRecord(timescale=self.timescale, time=dt, raw_value=value, unit='WH', source='homeflux.nut',
                            location=self.host_name, tags={'ip_address': self.ip_address})
            log.debug(repr(r))
        except KeyError:
            log.exception('NutError')
            raise(NutError('Failed to get key from NUT data'))

        if dc:
            await self.disconnect()

        return r
