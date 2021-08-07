"""Main Point of Entry"""
import time
import asyncio
import logging

from homeflux import environment
from homeflux.utils.timer import Timer
from homeflux.agents import gwp_opower, nut

log = logging.getLogger('homeflux.app')


async def nut_main():
    t = Timer()

    hosts = environment.NUT_HOSTS
    agents = []
    for host_name, ip_address in hosts.items():
        port = None
        if '@' in ip_address:
            ip_address, port = ip_address.split('@')
            port = int(port)
        agents.append(nut.NutClient(host_name, ip_address, 'second', port=port))

    for a in agents:
        t1 = Timer()
        async with a:
            await a.read()
        log.debug('Took %s to read from %s', t1.end(), a)

    log.debug('Took %s to read %s records from NUT', t.end(), len(agents))


async def gwp_main():
    t = Timer()
    m = gwp_opower.Meter(environment.GWP_USER, environment.GWP_PASSWORD, environment.GWP_UUID)
    async with m:
        power = await m.get_power_hourly()
        weather = await m.get_weather_hourly()

    log.debug('Took %s to read %s records from GWP', t.end(), len(power) + len(weather))


async def run_forever(coroutine, interval):
    while True:
        start = time.time()
        await coroutine()
        await asyncio.sleep(interval - (time.time() - start))


async def main():
    await asyncio.gather(run_forever(nut_main, 30),  # Run NUT loop every 30 seconds
                         run_forever(gwp_main, 21600))  # Run GWP loop every 6 hours=


if __name__ == '__main__':
    asyncio.run(main())
