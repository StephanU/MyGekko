# MyGekko

MyGekko integration for HomeAssistant using the [PyMyGekko](https://github.com/StephanU/PyMyGekko) library.

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Marketplace][marketplacebadge]][marketplace]
[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**This component will set up the following platforms.**

| Platform       | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `button`       | For light groups in MyGekko                                        |
| `camera`       | Cameras and door intercoms (called cams and door_intercom in MyGekko) |
| `climate`      | Thermostats (called roomtemps in MyGekko)                          |
| `cover`        | Covers (called blinds in MyGekko)                                  |
| `light`        | Lights                                                             |
| `switch`       | Switches (called loads in MyGekko)                                 |
| `water_heater` | Water Heater (called hotwater_systems in MyGekko)                  |
| `sensor`       | MyGekko energy_cost metrics, alarms_logics, room humidity and air quality, hot water temperatures, vent readings, weather station (meteo) and door intercom status |
| `scene`        | MyGekko actions are added as scenes                                |
| `select`       | Vent bypass, working mode and working level (called vents in MyGekko) |

![Dashboard Screenshot][dashboard-screenshot]

## Installation

### Via the Marketplace (Home Assistant 2026.11 and newer)

1. Go to "Settings" -> "Marketplace" and select "Add from link".
2. Enter `StephanU/MyGekko` under "GitHub link" and select "Add".
3. Open MyGekko and select "Install".
4. Set up the integration on the page that opens, or later under "Settings" -> "Devices & services" -> "Add integration" -> "MyGekko".

- Adding a repository by link requires a GitHub account connected to the Marketplace.

### Via HACS (Home Assistant 2026.10 and older)

1. Install [HACS](https://www.hacs.xyz/docs/use/).
2. Add `https://github.com/StephanU/MyGekko` as a [custom repository](https://www.hacs.xyz/docs/faq/custom_repositories/) of type "Integration".
3. Download MyGekko and restart Home Assistant.
4. Go to "Settings" -> "Devices & services" -> "Add integration" and search for "MyGekko".

### Manually

1. Download `mygekko_integration.zip` from the [latest release][releases].
2. Extract it into `custom_components/mygekko/` in your Home Assistant configuration directory (where `configuration.yaml` is). Afterwards `custom_components/mygekko/manifest.json` exists.
3. Restart Home Assistant.
4. Go to "Settings" -> "Devices & services" -> "Add integration" and search for "MyGekko".

## Configuration is done in the UI

When adding the integration, choose a connection type:

| Connection type          | Fields                         |
| ------------------------ | ------------------------------ |
| `MyGekko Plus Query API` | Username, Api Key, Gekko ID    |
| `Local`                  | IP Address, Username, Password |
| `Demo Mode`              | –                              |

- The MyGekko Plus Query API requires a MyGekko Plus subscription.
- Demo mode loads static data for all supported devices without connecting to a MyGekko.

To change the settings of an existing entry — IP address, credentials or even the connection type itself — open "Settings" -> "Devices & services" -> "MyGekko" and pick "Reconfigure" from the entry's menu.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Development Hints

- Start in VsCode in with the DevContainer extension
- execute `scripts/setup` to install dependencies
- execute `scripts/develop` to start HomeAssistant
- to use PyMyGekko from git instead of PyPi add the following to the .devcontainer
```
  "mounts": [
    "source=<local path to PyMyGekko>/PyMyGekko,target=/workspaces/PyMyGekko,type=bind"
  ]
```
- when the devcontainer is started:
```
 pip install -e /workspaces/PyMyGekko
```

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[buymecoffee]: https://www.buymeacoffee.com/stephanu
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/stephanu/mygekko.svg?style=for-the-badge
[commits]: https://github.com/stephanu/mygekko/commits/main
[marketplace]: https://www.home-assistant.io/integrations/marketplace/
[marketplacebadge]: https://img.shields.io/badge/Marketplace-Custom-orange.svg?style=for-the-badge
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
