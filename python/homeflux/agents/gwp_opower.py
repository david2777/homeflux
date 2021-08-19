"""Module for interacting with Glendale Water and Power gwp.opower.com JSON API"""
import json
import asyncio
import datetime
from typing import Union, Optional, List

from pyppeteer import launcher
from pyppeteer.page import Page

from homeflux import urls, environment, log
from homeflux.data.data_types import PowerRecord, ClimateRecord


class MeterError(Exception):
    pass


class Meter(object):
    """Class for interacting with Glendale Water and Power gwp.opower.com JSON API.

    """
    browser: Union[launcher.Browser, None] = None
    email: str
    password: str
    account_uuid: str

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

    @staticmethod
    async def screenshot(page: Page, force=False):
        """Screenshot the page to screenshots/ if DEBUG or force arg is True.

        Args:
            page (Page): Page to screenshot.
            force (Optional[bool]): Optionally set to True to force a screenshot.
        """
        pass
        # if environment.DEBUG or force:
        #     file_name = page.url.split('?')[0].split('.com/')[-1].replace('/', '.')
        #     try:
        #         await page.screenshot(path=f'{file_name}.png')
        #     except (FileNotFoundError, PermissionError, IOError, OSError):
        #         log.warning('Failed to write screenshot')

    async def get_raw_json_data(self, url: str) -> dict:
        """Return JSON data from a given URL.

        Args:
            url (str): URL to load JSON data from.

        Returns:
            dict: JSON data from URL.
        """
        if not self.browser:
            raise MeterError('Cannot _get_json without logging in')

        # Connect to page
        page = await self.browser.newPage()
        log.debug('Connecting to %s', url)
        await page.goto(url)
        await self.screenshot(page)

        # Grab the JSON data as a string
        data_elem = await page.querySelector('pre')
        data = await page.evaluate('(el) => el.textContent', data_elem)
        try:
            data = json.loads(data)
        except Exception:
            log.exception('Failed to read JSON from %s', url)
            return {}

        return data

    async def login(self):
        """Login to homeflux.opower.com and store the pyppeteer browser instance as self.browser.

        """
        log.info('Logging into GWP OPower')
        # Logout of the browser if it already exists
        if self.browser:
            log.debug('Already logged in, logging out...')
            await self.logout()

        browser_launch_config = {
            "defaultViewport": {"width": 1920, "height": 1080},
            "dumpio": False,
            "args": ["--no-sandbox"]}
        if environment.DOCKER:
            browser_launch_config['executablePath'] = '/usr/bin/google-chrome-stable'
        log.debug("browser_launch_config = %s", browser_launch_config)
        self.browser = await launcher.launch(browser_launch_config)
        log.debug('Launched browser at %s', repr(self.browser))

        # Navigate to login page
        log.debug('Opening a new page in browser')
        page = await self.browser.newPage()
        log.debug('Connecting to %s', urls.LOGIN)
        navigation_promise = asyncio.ensure_future(page.waitForNavigation())
        await page.goto(urls.LOGIN)
        await navigation_promise
        await self.screenshot(page)

        # Fill in login details and log in
        log.debug('Logging in...')
        await page.type('input[name="login"]', self.email)
        await page.type('input[name="password"]', self.password)
        navigation_promise = asyncio.ensure_future(page.waitForNavigation())
        await page.click('button[type="submit"]')
        await navigation_promise
        await self.screenshot(page)

    async def logout(self):
        """Log out of self.browser instance by closing the browser.

        """
        if not self.browser:
            log.info('No browser to close')
        log.info('Closing GWP OPower Browser')
        await self.browser.close()
        self.browser = None

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
