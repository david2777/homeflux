"""Module for interacting with Glendale Water and Power gwp.opower.com JSON API"""
import json
import datetime
from typing import Union, Optional, List

import requests

from homeflux import urls, environment, log
from homeflux.data.data_types import PowerRecord, ClimateRecord


class MeterError(Exception):
    pass


class Meter(object):
    """Class for interacting with Glendale Water and Power gwp.opower.com JSON API.

    """
    email: str
    password: str
    account_uuid: str
    session: Union[None, requests.Session]

    def __init__(self, email, password, account_uuid):
        """Initialize meter object (without logging in).

        Args:
            email (Str): Email for the account.
            password (str): Password for the account (plaintext since this is typed into the login forum).
            account_uuid (str): The account UUID, see docs for more details.
        """
        self.email = email
        self.password = password
        self.account_uuid = account_uuid

    async def __aenter__(self):
        await self.login()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.logout()

    async def get_raw_json_data(self, url: str) -> dict:
        """Return JSON data from a given URL.

        Args:
            url (str): URL to load JSON data from.

        Returns:
            dict: JSON data from URL.
        """
        if not self.session:
            raise MeterError('Cannot _get_json without logging in')

        data = self.session.get(url)
        data = data.content
        try:
            data = json.loads(data)
        except Exception:
            log.exception('Failed to read JSON from %s', url)
            return {}

        return data

    async def login(self):
        """Login to homeflux.opower.com and store the Session instance as self.session.

        """
        log.info('Logging into GWP OPower')
        self.session = requests.session()
        payload = "{\"username\":\"%s\",\"password\":\"%s\"}" % (environment.GWP_USER, environment.GWP_PASSWORD)
        self.session.post(urls.LOGIN, payload)

    async def logout(self):
        """Log out of Session instance by deleting it.

        """
        del self.session
        self.session = None

    async def get_data(self, raw_url: str, start_date_delta: int = -1, end_date_delta: int = 0) -> dict:
        """Return data from a given raw URL (from `homeflux.urls`) for the given date range. Note that you cannot
        request more then 30 days at a time.

        Args:
            raw_url  (str): URL from `homeflux.urls`
            start_date_delta (Optional[Int]): Start date in the from of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 1, yesterday.
            end_date_delta (Optional[Int]): End date in the form of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 0, today.

        Returns:
            dict: JSON data if it exists, empty dict if not.
        """
        try:
            # Get get start time and end time
            start_date = str(datetime.date.today() + datetime.timedelta(days=start_date_delta))
            end_date = str(datetime.date.today() + datetime.timedelta(days=end_date_delta))
            fmt = {'start_date': start_date, 'end_date': end_date, 'account_uuid': self.account_uuid, 'time': urls.TIME}
            url = raw_url.format(**fmt)
            data = await self.get_raw_json_data(url)

            if not data or not data['reads']:
                log.info('No reads found for dates %s - %s', start_date, end_date)
                return {}

            return data
        except Exception:
            log.exception('Runtime Error')
            return {}

    async def get_power_hourly(self, start_date_delta: int = -1, end_date_delta: int = 0) -> List[PowerRecord]:
        """Return a list of hourly power readings in the form of `MeterPower` objects from the given date range.

        Args:
            start_date_delta (Optional[Int]): Start date in the from of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 1, yesterday.
            end_date_delta (Optional[Int]): End date in the form of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 0, today.

        Returns:
            List[PowerRecord]: List of `MeterPower` objects for the given date range.
        """
        data = await self.get_data(urls.METER_HOURLY, start_date_delta, end_date_delta)
        result = []
        if not data:
            return result
        unit = data['units']['consumption']
        for read in data['reads']:
            if read['consumption']['type'] != 'ACTUAL':  # Skip non "ACTUAL" data, not sure if other data exists
                continue
            obj = PowerRecord(time=read['endTime'], raw_value=read['consumption']['value'], unit=unit, timescale='hour',
                              source='homeflux.gwp_opower', location='gwp_meter')
            log.debug(repr(obj))
            result.append(obj)

        return result

    async def get_weather_hourly(self, start_date_delta: int = -1, end_date_delta: int = 0) -> List[ClimateRecord]:
        """Return a list of hourly weather readings in the form of `MeterWeather` objects from the given date range.

        Args:
            start_date_delta (Optional[Int]): Start date in the from of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 1, yesterday.
            end_date_delta (Optional[Int]): End date in the form of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 0, today.

        Returns:
            List[ClimateRecord]: List of `MeterWeather` objects for the given date range.
        """
        data = await self.get_data(urls.WEATHER_HOURLY, start_date_delta, end_date_delta)
        result = []
        if not data:
            return []
        for read in data['reads']:
            obj = ClimateRecord(time=read['date'], raw_value=read['meanTemperature'], timescale='hour',
                                location='gwp_meter', source='homeflux.gwp_opower')
            log.debug(repr(obj))
            result.append(obj)

        return result
