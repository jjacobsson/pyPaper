
This is a collection of fairly simple python scripts that I run in order to drive my
WaveShare 7.5 inch e-paper display.

* poll.py is run continusly in a screen shell. It scrapes a REST endpoint the inverter for my solar power battery. It transforms the data some and saves it to a python pickle file (.status.db). It also prunes old entries from the pickle file.
* plot.py is run from cron every 2 minutes between 5:00 until 00:00. It reads the same pickle file and draws some graphs from the last 24 hours. This script has problems if the .status.db file exists, but does not contain any entries that fall in the last 24 hours.
* cls.py is run once a day 5 minutes past midnight, and all it does is wipe the e-paper display.

Below is an example of the json that the REST endpoint gives me.

```
{
  "Apparent_output": null,
  "BackupBuffer": "0",
  "BatteryCharging": false,
  "BatteryDischarging": false,
  "Consumption_Avg": 815,
  "Consumption_W": 543,
  "Fac": 50.013,
  "FlowConsumptionBattery": false,
  "FlowConsumptionGrid": true,
  "FlowConsumptionProduction": false,
  "FlowGridBattery": false,
  "FlowProductionBattery": false,
  "FlowProductionGrid": false,
  "GridFeedIn_W": -543.0,
  "IsSystemInstalled": 1,
  "OperatingMode": "2",
  "Pac_total_W": 2,
  "Production_W": 0,
  "RSOC": 8,
  "RemainingCapacity_Wh": 1634,
  "Sac1": null,
  "Sac2": null,
  "Sac3": null,
  "SystemStatus": "OnGrid",
  "Timestamp": "2024-11-15 22:14:47",
  "USOC": 0,
  "Uac": 234.0,
  "Ubat": 186.0,
  "dischargeNotAllowed": true,
  "generator_autostart": false
}
```