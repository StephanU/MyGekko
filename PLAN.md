# Plan: Stabilisierung, Optimierung, Erweiterung (PyMyGekko 1.6.0)

Ausgangslage: Updates "bleiben hängen", nach HA-Neustart kommen Werte, danach nicht mehr.
Ursachen laut Log + Opus-Reviews: HTTP 429 (Rate-Limit der Gekko-API), keine Timeouts,
verschluckte Fehler, Refresh-Sturm nach Schaltbefehlen, Reload-Listener-Leak, Kamera-Fehler.

## Phase 1 – Stabilität (erledigt)
| # | Maßnahme | Datei |
|---|----------|-------|
| 1 | Poll-Timeout, 429-Backoff (Intervall verdoppeln bis 5 min, danach zurück), Fehlertext mit Typ | coordinator.py |
| 2 | `async_write`: serialisiert, Mindestabstand, Retry bei 429, Timeout, `HomeAssistantError` | coordinator.py, alle Plattformen |
| 3 | Refresh nach Befehl mit 2 s Debounce statt 10 s Cooldown | coordinator.py |
| 4 | 403 -> `ConfigEntryAuthFailed`; `config_entry` an Coordinator | coordinator.py |
| 5 | Reload-Listener via `async_on_unload`, `async_reload` statt manuell | __init__.py |
| 6 | Zentrales Abfangen von Fehlern im State-Update je Entity | entity.py |
| 7 | Kamera: `CameraEntityFeature(0)`, geteilte Session, Timeout, `verify_ssl=False` | camera.py |
| 8 | Config-Flow: geteilte Session, Timeout, ClientError/TimeoutError | config_flow.py |
| 9 | Migration robust (kein KeyError, Downgrade-Schutz) | __init__.py |
| 10 | Sensor/Select/Light-Bugs (0-Werte, Top-Temp, Sound-Mode, VentWorkingLevel OFF, Farbmodus) | sensor/select/light.py |
| 11 | Deprecation `UnitOfRatio.PARTS_PER_MILLION` | sensor.py |

## Phase 2 – Optimierung
- Eindeutige Config-Entries (`unique_id` aus Gekko-ID bzw. IP) -> kein doppeltes Polling.
- Mindest-HA-Version in hacs.json an `homeassistant==2026.8.1` angleichen.

## Phase 3 – Erweiterung (neue Lib-Ressourcen)
- Energiemanager: Leistungs-/Energie-/Akku-Sensoren.
- E-Mobilität (Wallbox): Sensoren + Schalter Laden Start/Stop.
- Heizkreise: Temperatur-, Pumpen-, Ventil-Sensoren.
- Uhren (Zeitschaltuhren): Select (Aus/Ein/Bei Übereinstimmung).

## Nicht umgesetzt / Grenzen
- Lib-Fixes upstream (StephanU/PyMyGekko) nicht möglich -> Lib wurde stattdessen vendored (siehe unten).
- Zutrittstüren (Türöffner): bewusst nicht als Entity, sicherheitsrelevant.
- Tests: Template-Tests sind veraltet und lokal nicht lauffähig (HA 2026.8 braucht Python 3.14).

## Update: Lib vendored (superseded)
PyMyGekko 1.6.0 (MIT, Stephan Uhle) liegt jetzt in `custom_components/mygekko/pymygekko/` und wird nicht mehr
per pip installiert. Dadurch sind die Lib-Fixes in diesem Repo möglich:
HTTP-Timeouts (15 s), JSON-Fehler als `MyGekkoError`, atomares Lesen von Resources+Status,
defensive Zugriffe bei fehlenden Feldern, Subscriber-Fehler isoliert, Demo-Daten nicht im Event-Loop.

## Update: eigene API-Schicht (`custom_components/mygekko/api`)
PyMyGekko ist nicht mehr Teil des Repos. Die Integration nutzt eine eigene, abhängigkeitsfreie Schicht (MIT-Attribution im README,
Lizenzkopie in `api/LICENSE-PyMyGekko`):
- `schema.py`: deklarative Beschreibung aller Ressourcentypen (sumstate-Felder, Legacy-Varianten, Gruppen).
- `store.py`: generischer, fehlertoleranter Parser statt 17 Accessor-Klassen.
- `models.py`: Geräteklassen mit identischer öffentlicher API wie die Lib (Platforms unverändert bis auf Imports).
- `client.py`: Cloud-, Lokal- und Demo-Client, Timeouts, **nur `/var/status` pro Poll** (Namen werden gecacht), Fehler als Exceptions.
- Absicherung: Differenztest alte Lib vs. neue Schicht über alle Entities/Properties (192 Vergleiche, 0 Abweichungen) + `tests/test_api.py`.

## Update: Test gegen echtes Home Assistant
- Sandbox: Python 3.14 + HA 2026.8.1 und 2026.10.0 (aktuelle stabile Version) installiert; vorher war nichts gegen echtes HA gelaufen.
- Neue Testsuite (56 Tests, 94 % Coverage): Config-Flow (Cloud/Lokal/Demo, Duplikate, Reconfigure), Setup/Unload/Reload/Retry, Migration,
  Coordinator (429-Skips, Backoff, Recovery), alle Plattform-Dienste (Befehl/Wert), Befehlsserialisierung, Kameras/Intercom/Wetter, Diagnostics, API-Client.
- Gefundene und behobene Fehler: Beim ersten Abruf mit 429 wäre der Eintrag ohne Entities `LOADED` gewesen; Sensor-Setup (viele einzelne `add_entities`-Aufrufe,
  langsam); AQI-Sensor mit unzulässiger Einheit `%`; Wetter-Sensoren auch ohne Wetterstation; Kamera-Fehlermeldung.
- HA-Standards: `PARALLEL_UPDATES`, `integration_type`, Diagnostics (ohne Zugangsdaten), Reconfigure-Flow, hassfest 0 Fehler (2026.8.1 und 2026.10.0).
- CI: neuer Workflow `Tests` (gepinnt bei jedem PR; wöchentlich gegen stable und beta HA), Pins auf HA 2026.10.0.
