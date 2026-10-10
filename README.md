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

**This component will set up the following platforms.**

| Platform       | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `button`       | For light groups in MyGekko                                        |
| `climate`      | Thermostats (called roomtemps in MyGekko)                          |
| `cover`        | Covers (called blinds in MyGekko)                                  |
| `light`        | Lights                                                             |
| `switch`       | Switches (called loads in MyGekko)                                 |
| `water_heater` | Water Heater (called hotwater_systems in MyGekko)                  |
| `sensor`       | MyGekko energy_cost metrics and alarms_logics are added as sensors |
| `scene`        | MyGekko actions are added as scenes                                |
| `select`       | Vents settings and clocks (time switches)                          |
| `camera`       | Cams and door intercoms                                            |

Sensors are also provided for energy managers, e-mobility (wallbox, plus a charging switch) and heating circuits.

![Dashboard Screenshot][dashboard-screenshot]

## Installation

### Via HACS

1. Install [HACS](https://hacs.xyz/docs/setup/:requisites)
2. Add 'https://github.com/StephanU/MyGekko' as a [Custom Repository](https://hacs.xyz/docs/faq/custom_repositories)
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

## Configuration is done in the UI

The integration supports access via the MyGekko Query Api (you need a MyGekko Plus subscription) or by connecting to your MyGekko locally.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## How it works

- **Polling:** the integration polls `GET /api/v1/var/status` every 30 seconds. The document with the device names (`GET /api/v1/var`) is read once and refreshed every 30 minutes or when a new device appears, so only one request per poll is needed.
- **Rate limit:** the MyGekko Plus query API limits the number of requests. On HTTP 429 the poll interval is doubled (up to 5 minutes) and restored automatically once the API answers again. Commands are sent one after another and retried on 429.
- **Timeouts:** every request is bound by a timeout (15 s), a hanging device never blocks Home Assistant.
- **API layer (`custom_components/mygekko/api`):** `schema.py` describes the `sumstate` values of every resource type, `store.py` parses the API documents generically, `models.py` contains the device classes (`Light`, `Blind`, ...) and `client.py` the cloud, local and demo clients. There is no external dependency. To support a new resource type add a `ResourceSpec` in `schema.py` and a model class in `models.py`, then expose it in `client.py`.

## Development Hints

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
