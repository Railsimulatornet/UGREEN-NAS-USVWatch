# UGREEN NAS USVWatch

[![Python](https://github.com/Railsimulatornet/UGREEN-NAS-USVWatch/actions/workflows/python-checks.yml/badge.svg?branch=main)](https://github.com/Railsimulatornet/UGREEN-NAS-USVWatch/actions/workflows/python-checks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![USVWatch](Screens/USVWatch.png)

[Deutsch](#deutsch) · [English](#english)

## Deutsch

USVWatch liest den Zustand einer USV über den NUT-Dienst von UGOS Pro aus. Bei Ereignissen oder erreichten Schwellwerten versendet das Python-Skript einen Outlook-freundlichen HTML-Report per E-Mail.

### Funktionen

- NUT-Abfrage über den USV-Dienst, standardmäßig unter `127.0.0.1:3493`.
- Meldungen bei Batteriebetrieb, Rückkehr der Netzspannung, kritischer Batterie und Erreichbarkeitsproblemen.
- Einstellbare Schwellwerte für Akkuladung und verbleibende Laufzeit.
- Gespeicherter Status gegen wiederholte Meldungen, mit optionalem erneutem Versand.
- Optionaler Tagesreport zu einer festen Uhrzeit.
- Deutsche und englische Mailtexte über `USVWATCH_LANG`.
- NUT Instant Commands anzeigen und bei Bedarf ausführen.
- Einzellauf für Cron oder Hintergrundbetrieb über das mitgelieferte Loop-Skript.
- Python-Standardbibliothek; keine zusätzlichen Python-Pakete erforderlich.

### Voraussetzungen

- UGREEN NAS mit aktiviertem USV-/UPS-Dienst und erreichbarem NUT-Server.
- Python 3; der Loop verwendet standardmäßig `/usr/bin/python3`.
- Schreibrechte für Statusdateien, PID-Datei und Log.
- SMTP-Zugang für den Mailversand.

Die reine Statusabfrage und die Liste der NUT-Befehle benötigen keine SMTP-Konfiguration.

### Schnellstart

1. Lade das aktuelle Paket unter [Releases](https://github.com/Railsimulatornet/UGREEN-NAS-USVWatch/releases/latest) herunter.
2. Kopiere den **Inhalt** des Ordners `usvwatch/` direkt in deinen Zielordner, zum Beispiel `/volume2/docker/usvwatch/`.
3. Bearbeite dort `usvwatch.env`. Prüfe den NUT-Zugang und setze für den Mailversand mindestens `SMTP_HOST`, `MAIL_FROM` und `MAIL_TO`. Passe Port, TLS-Modus und Zugangsdaten an deinen Mailserver an.
4. Prüfe den aktuellen USV-Status und den Mailversand:

```bash
cd /volume2/docker/usvwatch
/usr/bin/python3 usvwatch.py --print-status
/usr/bin/python3 usvwatch.py --test-mail
```

5. Starte den Loop und kontrolliere Status und Log:

```bash
chmod +x usvwatch-loop.sh
./usvwatch-loop.sh start
./usvwatch-loop.sh status
./usvwatch-loop.sh tail
```

Die Pfade sind Beispiele. Der Zielordner enthält `usvwatch.py`, `usvwatch.env` und `usvwatch-loop.sh` direkt nebeneinander.

### Konfiguration

Die vollständige Konfiguration steht in [usvwatch/usvwatch.env](usvwatch/usvwatch.env).

| Bereich | Einstellungen |
| --- | --- |
| Sprache und Name | `USVWATCH_LANG=de` oder `USVWATCH_LANG=en`. `HOST_LABEL` ist optional; leer bedeutet System-Hostname. |
| Status und Diagnose | `STATE_DIR=.` für Statusdateien, `DEBUG=0` für deaktivierte Debug-Ausgaben. |
| NUT-Verbindung | `NUT_HOST=127.0.0.1`, `NUT_PORT=3493` und `NUT_TIMEOUT=5`. |
| USV-Auswahl | `NUT_UPS_NAME` kann bei einer einzelnen USV leer bleiben. |
| NUT-Anmeldung | `NUT_USERNAME` und `NUT_PASSWORD` passend zum Server setzen, falls eine Anmeldung erforderlich ist. |
| SMTP-Server | `SMTP_HOST`, `SMTP_PORT=587` und `SMTP_TIMEOUT=15`. |
| SMTP-TLS | `SMTP_TLS=starttls`, `ssl` oder `none`. Andere Werte werden vor dem SMTP-Verbindungsaufbau abgewiesen. `SMTP_TLS_VERIFY=1` aktiviert die Zertifikatsprüfung. |
| SMTP-Anmeldung | `SMTP_USER` und `SMTP_PASS`, wenn dein Server eine Anmeldung verlangt. |
| Mailadressen | `MAIL_FROM`, `MAIL_TO` sowie optional `MAIL_CC` und `MAIL_BCC`. Mehrere Empfänger werden durch Kommas getrennt. |
| Ereignisse | `ALERT_ON_BATTERY`, `ALERT_BACK_ONLINE`, `ALERT_LOW_BATTERY`, `ALERT_CHARGE_LOW`, `ALERT_RUNTIME_LOW`, `ALERT_UNREACHABLE` und `ALERT_RECOVERED`; jeweils `1` an oder `0` aus. |
| Schwellwerte | `CHARGE_THRESHOLD_PERCENT=20` und `RUNTIME_THRESHOLD_MIN=10`. |
| Erneuter Versand | `THRESHOLD_RESEND_MIN=60` und `UNREACHABLE_RESEND_MIN=120`; `0` deaktiviert die jeweilige Wiederholung. |
| Tagesreport | `ENABLE_DAILY_REPORT=0` und `DAILY_REPORT_TIME=09:00`. |
| Maildetails | `INCLUDE_ALL_VARS=1`, `INCLUDE_STATUS_LEGEND=1` und `ADD_HUMAN_STATUS_FIELD=1`. |
| Wertefilter | `ALL_VARS_INCLUDE_REGEX` und `ALL_VARS_EXCLUDE_REGEX` filtern die Tabelle mit den USV-Werten. |

Ein relativer `STATE_DIR` bezieht sich auf das aktuelle Arbeitsverzeichnis. Der Loop wechselt dafür in den Skriptordner. Bei eigenen Cron-Aufrufen solltest du ebenfalls zuerst in diesen Ordner wechseln oder einen absoluten Statuspfad setzen.

### Einzellauf und CLI

Ohne Parameter prüft das Skript genau einmal und eignet sich damit für Cron:

```bash
cd /volume2/docker/usvwatch
/usr/bin/python3 usvwatch.py
```

Eine andere ENV-Datei kannst du ausdrücklich angeben:

```bash
/usr/bin/python3 usvwatch.py --env /volume2/docker/usvwatch/usvwatch.env --test-mail
```

| Option | Funktion |
| --- | --- |
| `--print-status` | Aktuelle USV-Werte als JSON ausgeben. |
| `--test-mail` | Testmail senden. |
| `--list-commands` | Verfügbare NUT Instant Commands anzeigen. |
| `--run-cmd` | Einen ausgewählten Instant Command ausführen. |
| `--run-cmd-mail` | Nach `--run-cmd` zusätzlich einen Mailreport senden. |
| `--env` | Pfad zu einer anderen ENV-Datei festlegen. |

Prüfe zuerst die vom Gerät angebotenen Befehle:

```bash
/usr/bin/python3 usvwatch.py --list-commands
```

Beispiel für das Stummschalten des Signaltons, **nur wenn `beeper.mute` in der Liste verfügbar ist und du diese Änderung ausführen möchtest**:

```bash
/usr/bin/python3 usvwatch.py --run-cmd beeper.mute
```

Alternativ mit anschließendem Mailreport:

```bash
/usr/bin/python3 usvwatch.py --run-cmd beeper.mute --run-cmd-mail
```

### Loop-Betrieb

| Aufruf | Funktion |
| --- | --- |
| `./usvwatch-loop.sh start` | Hintergrundprozess starten. |
| `./usvwatch-loop.sh stop` | Hintergrundprozess stoppen. |
| `./usvwatch-loop.sh restart` | Stoppen und anschließend erneut starten. |
| `./usvwatch-loop.sh status` | Gespeicherten Prozessstatus prüfen. |
| `./usvwatch-loop.sh tail` | Die letzten 200 Logzeilen anzeigen. |

Zwischen den Läufen wartet der Loop standardmäßig 10 Sekunden. Die Wartezeit kannst du beim Start als Umgebungsvariable setzen; diese Option wird vom Wrapper nicht aus `usvwatch.env` geladen:

```bash
USVWATCH_LOOP_INTERVAL=30 ./usvwatch-loop.sh start
```

`USVWATCH_STOP_TIMEOUT` steuert die Wartezeit beim Stoppen, standardmäßig 15 Sekunden. `PYTHON` kann einen anderen Python-Pfad vorgeben. PID und Log liegen als `usvwatch.loop.pid` und `usvwatch-loop.log` im Skriptordner.

In einer frühen Wrapper-Version beendete `stop()` das Skript vor dem erneuten Start. Die aktuelle [usvwatch-loop.sh](usvwatch/usvwatch-loop.sh) enthält die Restart-Korrektur.

### Aktualisierung

Stoppe den Loop beziehungsweise pausiere Cron. Sichere die Skripte und deine Konfiguration, übernimm `usvwatch.py` und `usvwatch-loop.sh` aus dem neuen Paket und vergleiche neue ENV-Optionen. Behalte deine aktive `usvwatch.env` und gespeicherte Statusdateien. Prüfe danach Statusabfrage und Testmail und starte die Überwachung wieder.

### Screenshots

| Batteriebetrieb | Netzstrom wieder da |
| --- | --- |
| ![USVWatch: Stromausfall](Screens/USVWatchv1DE2.jpg) | ![USVWatch: Netzstrom wieder da](Screens/USVWatchv1DE.jpg) |

Ein [englischer Beispielreport](Screens/USVWatchv1EN.jpg) ist ebenfalls vorhanden.

### Projektstruktur und Dokumentation

| Pfad | Inhalt |
| --- | --- |
| [usvwatch/usvwatch.py](usvwatch/usvwatch.py) | NUT-Abfrage, Ereignisse und Mailversand. |
| [usvwatch/usvwatch.env](usvwatch/usvwatch.env) | Konfiguration. |
| [usvwatch/usvwatch-loop.sh](usvwatch/usvwatch-loop.sh) | Hintergrundbetrieb, Status und Loganzeige. |
| [Screens/](Screens/) | Projektbild und Beispielreports. |
| [USVWatch_Handbuch_Manual_DE-EN_v2.pdf](USVWatch_Handbuch_Manual_DE-EN_v2.pdf) | Ausführliches Handbuch auf Deutsch und Englisch. |

Aktuelles Paket: **V2.0.3**. Das Handbuch behält seinen bisherigen Dateinamen.

### Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

Copyright © 2026 **Roman Glos / Railsimulatornet**.

## English

USVWatch reads UPS status through the UGOS Pro NUT service. When events occur or thresholds are reached, the Python script sends an Outlook-friendly HTML report by email.

### Features

- NUT queries through the UPS service, using `127.0.0.1:3493` by default.
- Notifications for battery operation, restored mains power, a critical battery and reachability problems.
- Configurable thresholds for battery charge and remaining runtime.
- Stored state to limit repeated notifications, with optional resending.
- An optional daily report at a fixed time.
- German and English email text through `USVWATCH_LANG`.
- List NUT instant commands and execute selected commands when needed.
- One-time runs for cron or background operation through the included loop wrapper.
- Python standard library only; no additional Python packages are required.

### Requirements

- UGREEN NAS with its UPS service enabled and an accessible NUT server.
- Python 3; the wrapper uses `/usr/bin/python3` by default.
- Write access for state files, the PID file and the log.
- SMTP access for email delivery.

Status-only queries and listing NUT commands do not require SMTP configuration.

### Quick start

1. Download the current package from [Releases](https://github.com/Railsimulatornet/UGREEN-NAS-USVWatch/releases/latest).
2. Copy the **contents** of the `usvwatch/` folder directly to your destination, for example `/volume2/docker/usvwatch/`.
3. Edit `usvwatch.env` there. Check NUT access and set at least `SMTP_HOST`, `MAIL_FROM` and `MAIL_TO` for email delivery. Match the port, TLS mode and credentials to your mail server. Use `USVWATCH_LANG=en` for English emails.
4. Check current UPS status and email delivery:

```bash
cd /volume2/docker/usvwatch
/usr/bin/python3 usvwatch.py --print-status
/usr/bin/python3 usvwatch.py --test-mail
```

5. Start the wrapper and check its status and log:

```bash
chmod +x usvwatch-loop.sh
./usvwatch-loop.sh start
./usvwatch-loop.sh status
./usvwatch-loop.sh tail
```

The paths are examples. The destination contains `usvwatch.py`, `usvwatch.env` and `usvwatch-loop.sh` directly beside each other.

### Configuration

The complete configuration is provided in [usvwatch/usvwatch.env](usvwatch/usvwatch.env).

| Area | Settings |
| --- | --- |
| Language and name | `USVWATCH_LANG=de` or `USVWATCH_LANG=en`. `HOST_LABEL` is optional; empty means the system hostname. |
| State and diagnostics | `STATE_DIR=.` for state files; `DEBUG=0` disables debug output. |
| NUT connection | `NUT_HOST=127.0.0.1`, `NUT_PORT=3493` and `NUT_TIMEOUT=5`. |
| UPS selection | `NUT_UPS_NAME` can stay empty when there is only one UPS. |
| NUT login | Set `NUT_USERNAME` and `NUT_PASSWORD` to match your server if authentication is required. |
| SMTP server | `SMTP_HOST`, `SMTP_PORT=587` and `SMTP_TIMEOUT=15`. |
| SMTP TLS | `SMTP_TLS=starttls`, `ssl` or `none`. Other values are rejected before opening the SMTP connection. `SMTP_TLS_VERIFY=1` enables certificate verification. |
| SMTP login | `SMTP_USER` and `SMTP_PASS` if your server requires authentication. |
| Email addresses | `MAIL_FROM`, `MAIL_TO` and optional `MAIL_CC` and `MAIL_BCC`. Separate multiple recipients with commas. |
| Events | `ALERT_ON_BATTERY`, `ALERT_BACK_ONLINE`, `ALERT_LOW_BATTERY`, `ALERT_CHARGE_LOW`, `ALERT_RUNTIME_LOW`, `ALERT_UNREACHABLE` and `ALERT_RECOVERED`; `1` enables and `0` disables each event. |
| Thresholds | `CHARGE_THRESHOLD_PERCENT=20` and `RUNTIME_THRESHOLD_MIN=10`. |
| Resending | `THRESHOLD_RESEND_MIN=60` and `UNREACHABLE_RESEND_MIN=120`; `0` disables the respective repeat. |
| Daily report | `ENABLE_DAILY_REPORT=0` and `DAILY_REPORT_TIME=09:00`. |
| Email details | `INCLUDE_ALL_VARS=1`, `INCLUDE_STATUS_LEGEND=1` and `ADD_HUMAN_STATUS_FIELD=1`. |
| Value filters | `ALL_VARS_INCLUDE_REGEX` and `ALL_VARS_EXCLUDE_REGEX` filter the UPS-value table. |

A relative `STATE_DIR` refers to the current working directory. The wrapper changes into the script directory. For custom cron commands, also change to that directory first or set an absolute state path.

### One-time runs and CLI

Without arguments, the script checks once, making it suitable for cron:

```bash
cd /volume2/docker/usvwatch
/usr/bin/python3 usvwatch.py
```

You can explicitly select a different ENV file:

```bash
/usr/bin/python3 usvwatch.py --env /volume2/docker/usvwatch/usvwatch.env --test-mail
```

| Option | Function |
| --- | --- |
| `--print-status` | Print current UPS values as JSON. |
| `--test-mail` | Send a test email. |
| `--list-commands` | List available NUT instant commands. |
| `--run-cmd` | Execute a selected instant command. |
| `--run-cmd-mail` | Send an additional email report after `--run-cmd`. |
| `--env` | Set the path to another ENV file. |

First check which commands the device provides:

```bash
/usr/bin/python3 usvwatch.py --list-commands
```

Example for muting the beeper, **only if `beeper.mute` is listed and you intend to make this change**:

```bash
/usr/bin/python3 usvwatch.py --run-cmd beeper.mute
```

Alternatively, send an email report afterwards:

```bash
/usr/bin/python3 usvwatch.py --run-cmd beeper.mute --run-cmd-mail
```

### Loop operation

| Command | Function |
| --- | --- |
| `./usvwatch-loop.sh start` | Start the background process. |
| `./usvwatch-loop.sh stop` | Stop the background process. |
| `./usvwatch-loop.sh restart` | Stop, then start again. |
| `./usvwatch-loop.sh status` | Check the recorded process status. |
| `./usvwatch-loop.sh tail` | Show the last 200 log lines. |

The wrapper waits 10 seconds between runs by default. Set a different delay as an environment variable when starting it; the wrapper does not load this setting from `usvwatch.env`:

```bash
USVWATCH_LOOP_INTERVAL=30 ./usvwatch-loop.sh start
```

`USVWATCH_STOP_TIMEOUT` controls the stop wait, defaulting to 15 seconds. `PYTHON` can specify a different Python path. The PID file and log are stored as `usvwatch.loop.pid` and `usvwatch-loop.log` in the script directory.

In an early wrapper version, `stop()` exited before the restart could proceed. The current [usvwatch-loop.sh](usvwatch/usvwatch-loop.sh) includes the restart correction.

### Updating

Stop the loop or pause cron. Back up the scripts and configuration, take `usvwatch.py` and `usvwatch-loop.sh` from the new package and compare new ENV settings. Keep your active `usvwatch.env` and stored state files. Then check the status query and test email and restart monitoring.

### Screenshots

![USVWatch: English sample report](Screens/USVWatchv1EN.jpg)

German examples show [battery operation](Screens/USVWatchv1DE2.jpg) and [restored mains power](Screens/USVWatchv1DE.jpg).

### Project structure and documentation

| Path | Contents |
| --- | --- |
| [usvwatch/usvwatch.py](usvwatch/usvwatch.py) | NUT queries, events and email delivery. |
| [usvwatch/usvwatch.env](usvwatch/usvwatch.env) | Configuration. |
| [usvwatch/usvwatch-loop.sh](usvwatch/usvwatch-loop.sh) | Background operation, status and log output. |
| [Screens/](Screens/) | Project image and sample reports. |
| [USVWatch_Handbuch_Manual_DE-EN_v2.pdf](USVWatch_Handbuch_Manual_DE-EN_v2.pdf) | Detailed German and English manual. |

Current package: **V2.0.3**. The manual retains its existing filename.

### License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 **Roman Glos / Railsimulatornet**.

