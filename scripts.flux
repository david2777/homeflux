START TIME: 2019-06-01T00:00:00-07:00

Weekly Tasks:
from(bucket: "climate_hourly")
  |> range(start: -2w)
  |> filter(fn: (r) => r["_measurement"] == "temperature")
  |> aggregateWindow(every:  1w, fn: mean)
  |> to(bucket: "climate_weekly")

from(bucket: "power_hourly")
  |> range(start: -2w)
  |> filter(fn: (r) => r["_measurement"] == "power_usage")
  |> aggregateWindow(every:  1w, fn: sum)
  |> to(bucket: "power_weekly")

Daily Tasks:
from(bucket: "climate_hourly")
  |> range(start: -2d)
  |> filter(fn: (r) => r["_measurement"] == "temperature")
  |> aggregateWindow(every:  1d, fn: mean)
  |> to(bucket: "climate_daily")

from(bucket: "power_hourly")
  |> range(start: -2d)
  |> filter(fn: (r) => r["_measurement"] == "power_usage")
  |> aggregateWindow(every:  1d, fn: sum)
  |> to(bucket: "power_daily")

Hourly Tasks:
from(bucket: "power_minutely")
  |> range(start: -2h)
  |> filter(fn: (r) => r["_measurement"] == "power_usage")
  |> aggregateWindow(every:  1h, fn: mean)

Minutely Tasks:
from(bucket: "nut_raw")
	|> range(start: -5m)
	|> filter(fn: (r) =>
		(r["_measurement"] == "ups"))
	|> filter(fn: (r) =>
		(r["_field"] == "ups.load"))
	|> rename(columns: {host: "meter"})
	|> map(fn: (r) =>
		({r with _value: float(v: r._value) * 5.1, _measurement: "power_usage", meter: r.meter + "_nut"}))
	|> drop(columns: ["hardware", "model"])
	|> to(bucket: "power_minutely")
