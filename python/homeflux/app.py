"""Main Point of Entry"""
import time
import asyncio

from homeflux import environment, log
from homeflux.utils.timer import Timer
from homeflux.data import database as db
from homeflux.agents import gwp_opower, nut


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


async def run_forever(coroutine, interval: int):
    """Routine to run a function coroutine on an interval forever.

    Args:
        coroutine: The coroutine to run.
        interval (int): Interval to run on.

    """
    while True:
        start = time.time()
        await coroutine()
        await asyncio.sleep(interval - (time.time() - start))


async def main():
    """Main function, run all of the agents on the specified intervals.

    """
    await asyncio.gather(run_forever(nut_main, 60),  # Run NUT loop every 60 seconds
                         run_forever(gwp_main, 21600))  # Run GWP loop every 6 hours


if __name__ == '__main__':
    # from homeflux.utils import db_utils
    # db_utils.generate_buckets(True)
    asyncio.run(main())
