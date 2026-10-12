[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

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
| `camera`        | Cameras and door intercoms (image and stream)                                                                        |

The alarm system and the door/gate openers are deliberately **read only**: they can be monitored but not armed, disarmed or opened from Home Assistant.

**Highlights**

- Every device belongs to the MyGekko controller device (model, software version and link to the web interface).
- Optional: use the pages of the MyGekko app (floor, room) as Home Assistant areas.
- Careful with the cloud rate limit: one request per poll, a 4 minute pause on HTTP 429 (entities always keep their last state, also across restarts), configurable update interval and a repair hint if the limit persists.
- The myGEKKO controller device shows the API status, the last update and the end of a rate limit pause; a MyGekko that is set up twice is reported as repair issue.
- Elements that are locked, in manual operation or in alarm show an `element_status` attribute.
- Re-authentication, reconfiguration, diagnostics download (credentials are redacted) and a demo mode that needs no MyGekko.
- Translated into English, German, French, Italian and Norwegian.

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
