"""URL Constants"""
LOGIN = "https://gwp.opower.com/ei/x/sign-in-wall"

METER_HOURLY = 'https://gwp.opower.com/ei/edge/apis/DataBrowser-v1/cws/utilities/gwp/utilityAccounts/' \
               '{account_uuid}/reads?startDate={start_date}&endDate={end_date}&aggregateType=hour'

WEATHER_HOURLY = 'https://gwp.opower.com/ei/edge/apis/DataBrowser-v1/cws/weather/hourly?' \
                 'startDate={start_date}{time}&endDate={end_date}{time}&useCelsius=false'

TIME = 'T00:00:00-07:00'.replace(':', '%3A')
