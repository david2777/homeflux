"""URL Constants"""
import time

LOGIN = "https://gwp.opower.com/ei/edge/apis/user-account-control-v1/cws/v1/gwp/account/signin"

METER_HOURLY = 'https://gwp.opower.com/ei/edge/apis/DataBrowser-v1/cws/utilities/gwp/utilityAccounts/' \
               '{account_uuid}/reads?startDate={start_date}&endDate={end_date}&aggregateType=hour'

METER_DAILY = 'https://gwp.opower.com/ei/edge/apis/DataBrowser-v1/cws/utilities/gwp/utilityAccounts/' \
               '{account_uuid}/reads?startDate={start_date}&endDate={end_date}&aggregateType=day'

WEATHER_HOURLY = 'https://gwp.opower.com/ei/edge/apis/DataBrowser-v1/cws/weather/hourly?' \
                 'startDate={start_date}{time}&endDate={end_date}{time}&useCelsius=false'

WEATHER_DAILY = 'https://gwp.opower.com/ei/edge/apis/DataBrowser-v1/cws/weather/daily?' \
                'startDate={start_date}&endDate={end_date}&useCelsius=false'

UTC_OFFSET = time.localtime().tm_gmtoff / 3600
if UTC_OFFSET < 0:
    UTC_OFFSET = f'{UTC_OFFSET:06.02f}'.replace('.', ':')
else:
    UTC_OFFSET = f'{UTC_OFFSET:05.02f}'.replace('.', ':')

TIME = f'T00:00:00{UTC_OFFSET}'.replace(':', '%3A')

