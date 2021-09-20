"""Module for interacting with Glendale Water and Power gwp.opower.com JSON API"""
import json
import datetime
from typing import Union, Optional, List

import requests
import requests_mock

from homeflux import urls, environment, log
from homeflux.data.data_types import PowerRecord, ClimateRecord


class MeterError(Exception):
    pass


class Meter:
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
        self.session = None

    async def __aenter__(self):
        await self.login()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.logout()

    async def login(self):
        """Login to homeflux.opower.com and store the Session instance as self.session.

        """
        log.info('Logging into GWP OPower')
        self.session = requests.session()
        login_url = urls.LOGIN
        if environment.TEST:
            login_url = login_url.replace('https://', 'mock://')
            adapter = requests_mock.Adapter()
            self.session.mount('mock://', adapter)
            adapter.register_uri('POST', login_url, text='data')
        payload = "{\"username\":\"%s\",\"password\":\"%s\"}" % (environment.GWP_USER, environment.GWP_PASSWORD)
        log.debug('POSTing to %s', login_url)
        r = self.session.post(login_url, payload)
        log.debug('Response Code: %s', r.status_code)
        if r.status_code not in [200, 204]:
            raise MeterError('Failed to login, response code: {}'.format(r.status_code))

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
        if not self.session:
            raise MeterError('Cannot _get_json without logging in')

        try:
            # Get get start time and end time
            start_date = str(datetime.date.today() + datetime.timedelta(days=start_date_delta))
            end_date = str(datetime.date.today() + datetime.timedelta(days=end_date_delta))
            fmt = {'start_date': start_date, 'end_date': end_date, 'account_uuid': self.account_uuid, 'time': urls.TIME}
            url = raw_url.format(**fmt)

            log.debug('Connecting to %s', url)
            r = self.session.get(url)
            log.debug('Response Code: %s', r.status_code)
            if r.status_code != 200:
                log.error('Response Code: %s', r.status_code)
                return {}
            data = r.content
            try:
                data = json.loads(data)
            except Exception:
                log.exception('Failed to read JSON from %s', url)
                return {}

            if not data or not data.get('reads'):
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
    
    async def get_power_daily(self, start_date_delta: int = -3, end_date_delta: int = -1) -> List[PowerRecord]:
        """Return a list of daily power readings in the form of `MeterPower` objects from the given date range.

        Args:
            start_date_delta (Optional[Int]): Start date in the from of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 1, yesterday.
            end_date_delta (Optional[Int]): End date in the form of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 0, today.

        Returns:
            List[PowerRecord]: List of `MeterPower` objects for the given date range.
        """
        data = await self.get_data(urls.METER_DAILY, start_date_delta, end_date_delta)
        result = []
        if not data:
            return result
        unit = data['units']['consumption']
        for read in data['reads']:
            obj = PowerRecord(time=read['endTime'], raw_value=read['consumption']['value'], unit=unit, timescale='day',
                              source='homeflux.gwp_opower', location='gwp_meter')
            log.debug(repr(obj))
            result.append(obj)

        return result

    async def get_weather_daily(self, start_date_delta: int = -3, end_date_delta: int = -1) -> List[ClimateRecord]:
        """Return a list of daily weather readings in the form of `MeterWeather` objects from the given date range.

        Args:
            start_date_delta (Optional[Int]): Start date in the from of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 1, yesterday.
            end_date_delta (Optional[Int]): End date in the form of number of days from today. Eg 0 is today, -1 is
            yesterday, -2 is two days ago, etc. Default is 0, today.

        Returns:
            List[ClimateRecord]: List of `MeterWeather` objects for the given date range.
        """
        data = await self.get_data(urls.WEATHER_DAILY, start_date_delta, end_date_delta)
        result = []
        if not data:
            return []
        for read in data['reads']:
            obj = ClimateRecord(time=read['date'].replace('.000Z', urls.UTC_OFFSET), raw_value=read['meanTemperature'],
                                timescale='day', location='gwp_meter', source='homeflux.gwp_opower')
            log.debug(repr(obj))
            result.append(obj)

        return result
