"""Main Point of Entry"""
import asyncio

import aiocron

from homeflux import environment, log
from homeflux.utils.timer import Timer
from homeflux.data import database as db
from homeflux.agents import gwp_opower, nut


@aiocron.crontab('*/1 * * * *')  # Run every minute
async def nut_main():
    """Main NUT gather loop, designed to run forever on an interval.

    """
    t = Timer()

    hosts = environment.NUT_HOSTS
    agents = []
    for host_name, ip_address in hosts.items():
        port = None
        if '@' in ip_address:
            ip_address, port = ip_address.split('@')
            port = int(port)
        agents.append(nut.NutClient(host_name, ip_address, 'minute', port=port))

    reads = []

    for a in agents:
        t1 = Timer()
        try:
            async with a:
                read = await a.read()
                if read:
                    reads.append(read)
        except nut.NutError:
            log.exception('Could not connect to %s', a.ip_address)
        else:
            log.debug('Took %s to read from %s', t1.end(), a)

    log.info('Took %s seconds to read %s records from NUT', t.end(), len(reads))

    if not environment.DRY_RUN:
        db.write(values=reads)


@aiocron.crontab('0 */8 * * *')  # Run every 8 hours (aka 3x per day) just in case
async def gwp_main():
    """Main GWP gather loop, designed to run forever on an interval.

    """
    t = Timer()
    m = gwp_opower.Meter(environment.GWP_USER, environment.GWP_PASSWORD, environment.GWP_UUID)
    try:
        async with m:
            power_hourly = await m.get_power_hourly()
            weather_hourly = await m.get_weather_hourly()
            power_daily = await m.get_power_daily()
            weather_daily = await m.get_weather_daily()
    except gwp_opower.MeterError:
        log.exception('Could not connect to GWP Meter')
    else:
        log.info('Took %s seconds to read %s records from GWP OPower', t.end(),
                 len(power_hourly) + len(weather_hourly) + len(power_daily) + len(weather_daily))

    if not environment.DRY_RUN:
        db.write(values=power_hourly)
        db.write(values=weather_hourly)
        db.write(values=power_daily)
        db.write(values=weather_daily)


def run_once():
    asyncio.run(gwp_main.func())
    asyncio.run(nut_main.func())


def main():
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
