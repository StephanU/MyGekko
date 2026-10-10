# MyGekko

MyGekko integration for Home Assistant. It talks to the MyGekko REST API directly with its own, dependency-free API layer (`custom_components/mygekko/api`), which is derived from [PyMyGekko](https://github.com/StephanU/PyMyGekko) (see [Credits](#credits)).

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![hacs][hacsbadge]][hacs]
[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**This integration sets up the following platforms.**

| Platform        | What you get                                                                                                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------- |
| `light`         | Lights and light groups (on/off, brightness, RGB)                                                                    |
| `cover`         | Blinds with position and slat angle, blind groups                                                                    |
| `climate`       | Room controllers with target temperature, presets, humidity and heating/cooling action                               |
| `switch`        | Loads, and the charging switch of a wallbox                                                                          |
| `water_heater`  | Hot water systems                                                                                                    |
| `select`        | Ventilation settings and clocks (time switches)                                                                      |
| `scene`         | MyGekko actions as scenes                                                                                            |
| `button`        | Light group buttons                                                                                                  |
| `sensor`        | Energy meters, energy manager (grid, solar, battery), wallbox, heating circuits and systems, ventilation, floor temperature, weather station, multiroom audio, trends, alarms and logics |
| `binary_sensor` | Doors and gates (open), alarm system and zones (read only), wallbox plugged in, load shedding, heating running/cooling, notifications |
| `alarm_control_panel` | One panel per zone of the alarm system (disarmed / armed / triggered), read only |
| `camera`        | Cameras and door intercoms (image and stream)                                                                        |

The alarm system is deliberately **read only**: it can be monitored but not armed or disarmed from Home Assistant. Doors, gates and barriers get an **Open** button which is **disabled by default**: enable it on purpose in the entity settings and do not expose it to voice assistants.

**Highlights**

- Every device belongs to the MyGekko controller device (model, software version and link to the web interface).
- Optional: use the pages of the MyGekko app (floor, room) as Home Assistant areas.
- Careful with the cloud rate limit: one request per poll, automatic back-off on HTTP 429 (entities keep their values), configurable update interval and a repair hint if the limit persists.
- Elements that are locked, in manual operation or in alarm show an `element_status` attribute.
- Re-authentication, reconfiguration, diagnostics download (credentials are redacted) and a demo mode that needs no MyGekko.
- Translated into English, German, French, Italian and Norwegian.

![Dashboard Screenshot][dashboard-screenshot]

## Installation

### Via HACS

1. Install [HACS](https://hacs.xyz/docs/setup/:requisites)
2. Add 'https://github.com/merlin2533/MyGekko' as a [Custom Repository](https://hacs.xyz/docs/faq/custom_repositories)
3. Restart Home Assistant
4. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "MyGekko"

### Manually

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `mygekko`.
4. Download _all_ the files from the `custom_components/mygekko/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "MyGekko"

Using your HA configuration directory (folder) as a starting point you should now also have something like this:

```text
custom_components/mygekko/__init__.py
custom_components/mygekko/api/
custom_components/mygekko/config_flow.py
custom_components/mygekko/coordinator.py
custom_components/mygekko/manifest.json
custom_components/mygekko/translations/
... (one file per platform: sensor.py, light.py, cover.py, ...)
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Configuration

The integration supports the MyGekko Plus query API (cloud, needs a MyGekko Plus subscription), the local API of your MyGekko and a demo mode with static data.

- **Options** (integration → Configure): update interval (default 30 s, minimum 10 s) and "use the MyGekko pages as areas".
- **Local connection:** the integration tries https first and falls back to http (older firmware or a MyGekko without https). Only a refused connection or a failed SSL handshake triggers the fallback (not a timeout). With http the login travels unencrypted over your local network (a warning is logged), so use it only in a trusted network. The scheme is detected again when you reconfigure the entry.
- **Reconfigure** (integration → three dots): change credentials or the IP address without removing the integration.
- If MyGekko rejects the credentials Home Assistant asks for them again (re-authentication).
- **Troubleshooting:** download the diagnostics of the integration (credentials, Gekko ID and IP address are redacted) and attach them to an issue. Rate limit warnings (`skipping this update`) mean that MyGekko limits the requests: increase the update interval and avoid automations that switch devices in a fast loop.

## Breaking changes

**1.4.0: climate presets.** The presets of the room controllers now have readable ids: `off`, `comfort`, `reduced`, `manual`, `standby` (before: `1`, `8`, `16`, `64`, `256`). Update automations, scripts and dashboards that call `climate.set_preset_mode` or compare `preset_mode` with the old numbers. The displayed names are translated as before.

**1.5.0: room controllers** can be switched off and on with the standard heating mode buttons (`off` / `auto`); `auto` switches a controller that is off back to comfort. The presets are unchanged.

## Home Assistant versions

The integration checks which Home Assistant it runs on and uses the matching API: from Home Assistant 2026.11 the `native_*` temperature properties of climate and water heater entities (no deprecation warnings), before that the previous names. It is tested against Home Assistant 2026.8, the current release and the development version of the next release. The diagnostics show the versions in use.

## How it works

- **Polling:** the integration polls `GET /api/v1/var/status` every 30 seconds. The document with the device names (`GET /api/v1/var`) is read once and refreshed every 30 minutes or when a new device appears, so only one request per poll is needed.
- **Rate limit:** the MyGekko Plus query API limits the number of requests. On HTTP 429 the poll interval is doubled (up to 5 minutes) and restored automatically once the API answers again. Commands are sent one after another and retried on 429.
- **Timeouts:** every request is bound by a timeout (15 s), a hanging device never blocks Home Assistant.
- **API layer (`custom_components/mygekko/api`):** `schema.py` describes the `sumstate` values of every resource type, `store.py` parses the API documents generically, `models.py` contains the device classes (`Light`, `Blind`, ...) and `client.py` the cloud, local and demo clients. There is no external dependency. To support a new resource type add a `ResourceSpec` in `schema.py` and a model class in `models.py`, then expose it in `client.py`.

## Testing

The tests run against a real Home Assistant (`pytest-homeassistant-custom-component`), they set up the integration in demo mode, send commands through the Home Assistant services and cover the config flow, the polling/rate-limit behavior and the API layer.

```bash
python3.14 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest tests
```

The GitHub workflow `Tests` runs this on every pull request with the Home Assistant version from `requirements.txt`, and weekly against the newest stable and the beta Home Assistant to find upcoming incompatibilities early. `Validate` runs hassfest and the HACS validation daily.

## Development Hints

- `scripts/test-ha-dev` runs the tests against the development version of Home Assistant (needs a checkout of home-assistant/core, see the header of the script)

- Start in VsCode in with the DevContainer extension
- execute `scripts/setup` to install dependencies
- execute `scripts/develop` to start HomeAssistant
- `tests/test_api.py` tests the API layer against a fake MyGekko server; the layer itself has no Home Assistant dependency

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

The API layer in `custom_components/mygekko/api` is derived from [PyMyGekko](https://github.com/StephanU/PyMyGekko) by Stephan Uhle (MIT License, copy in [`custom_components/mygekko/api/LICENSE-PyMyGekko`](custom_components/mygekko/api/LICENSE-PyMyGekko)). The device models, the field layout of the MyGekko `sumstate` values and the command formats originate from that library; the parser, the client and the polling strategy were rewritten.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/stephanu
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/stephanu/mygekko.svg?style=for-the-badge
[commits]: https://github.com/stephanu/mygekko/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[dashboard-screenshot]: DashboardScreenshot.png
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/stephanu/mygekko.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40stephanu-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/stephanu/mygekko.svg?style=for-the-badge
[releases]: https://github.com/stephanu/mygekko/releases
[user_profile]: https://github.com/stephanu
