[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

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

![Dashboard Screenshot][dashboard-screenshot]

{% if not installed %}

## Installation

1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "MyGekko".

{% endif %}

## Configuration is done in the UI

The integration supports access via the MyGekko Query Api (you need a MyGekko Plus subscription) or by connecting to your MyGekko locally.

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
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
[license]: https://github.com/stephanu/mygekko/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/stephanu/mygekko.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40stephanu-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/stephanu/mygekko.svg?style=for-the-badge
[releases]: https://github.com/stephanu/mygekko/releases
[user_profile]: https://github.com/stephanu
