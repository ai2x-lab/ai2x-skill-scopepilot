# Profile Spec

Use one JSON file per vendor under `vendor_profiles/`.

Minimum fields:

- `idn_match`
- `channel_format`
- `value_map`
- `scale_rules`
- `commands`
- `capabilities`

`scale_rules` defines legal scope scale steps. Use decade-based sequences such as `1-2-5`.

Example:

```json
"scale_rules": {
  "vertical": {
    "sequence": [1, 2, 5],
    "min": 0.001,
    "max": 10.0,
    "unit": "V/div"
  },
  "time": {
    "sequence": [1, 2, 5],
    "min": 1e-9,
    "max": 50.0,
    "unit": "s/div"
  }
}
```

`commands` currently supports:

- `identify`
- `run_acquisition`
- `stop_acquisition`
- `set_channel_display`
- `set_vertical_scale`
- `set_time_scale`
- `measure_source`
- `measure.vpp`
- `measure.frequency`
- `measure.vrms`
- `capture.setup`
- `capture.query_binary`

Example:

```json
{
  "idn_match": ["KEYSIGHT"],
  "channel_format": "CHAN{index}",
  "value_map": {
    "on": "1",
    "off": "0"
  },
  "commands": {
    "identify": "*IDN?",
    "set_channel_display": ":{channel}:DISPLAY {value}",
    "set_vertical_scale": ":{channel}:SCALE {value}"
  }
}
```
