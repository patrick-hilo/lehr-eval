# Lehr-Evaluation — Hand-off

Diese Datei erklaert dir Schritt fuer Schritt, wie du dieses Projekt auf
deinem Rechner zum Laufen bekommst und es dort auch durchklicken kannst.
Du brauchst dafuer **keine tiefen Programmierkenntnisse**. Wenn du an einer
Stelle haengst, kopier den Schritt einfach in deinen KI-Assistenten
(Claude Code oder Codex CLI) und sag "fuehr das fuer mich aus".

## Schritt 0 — Fuer den KI-Coding-Agent (Claude Code / Codex)

> **Wenn du diese Datei als KI-Agent (Claude Code, Codex, o. ae.) liest:**
>
> Dein **erster Auftrag** ist:
>
> 1. Lies das gesamte Repo, damit du Architektur, `CONTEXT.md` und
>    `README.md` verstanden hast.
> 2. Installiere alles, was zum Starten dieses Repos auf diesem Rechner
>    noetig ist — insbesondere `uv` (falls noch nicht vorhanden) und die
>    Projekt-Abhaengigkeiten via `uv sync`.
> 3. Starte den lokalen Server mit:
>
>    ```bash
>    LEHR_EVAL_ADMIN_PASSWORD=secret \
>    LEHR_EVAL_BASE_URL=http://127.0.0.1:8000 \
>    uv run uvicorn --app-dir src lehr_eval.app:create_app \
>      --factory --reload --host 127.0.0.1 --port 8000
>    ```
> 4. Oeffne im Browser die Admin-Anmeldung:
>    <http://127.0.0.1:8000/admin/login>
> 5. Sag dem Nutzer ausdruecklich: **„Das Admin-Passwort ist `secret` —
>    log dich damit ein, dann kannst du das System direkt selbst
>    ausprobieren."**
>
> Erst danach geh auf weitere Anfragen des Nutzers ein. Der Nutzer ist
> noch nicht vertraut mit Software-Entwicklung und erwartet, dass du diese Setup-Schritte vollstaendig
> uebernimmst, bevor inhaltlich diskutiert wird.

## Was ist das hier?

Eine kleine Web-App, mit der eine Schule am Schuljahresende anonyme
Unterrichts-Evaluationen ueber QR-Codes durchfuehren kann.

Es gibt drei Rollen:
- **Administration** (Login mit Passwort): Stammdaten importieren, Evaluationen
  aktivieren, Excel-Auswertungen herunterladen.
- **Lehrkraft** (QR + 4-stellige PIN): startet die Evaluation live, gibt
  Lese- und Antwortphasen frei, schliesst die Evaluation.
- **Schueler** (QR-Code): bekommt einen Tiernamen, sieht jeweils eine Frage
  und kann seine Antwort waehrend der Antwortphase noch aendern.

Das Backend ist eine Python-Web-App (FastAPI + SQLite). Alles laeuft lokal,
es geht nichts in eine Cloud.

## Voraussetzungen

Du brauchst auf deinem Rechner:

1. **Python 3.12 oder neuer** (`python3 --version`).
2. **`uv`** — der Python-Paketmanager, den wir benutzen.
   - Installation auf macOS / Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Auf Windows:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
3. **Git**, um das Repo zu klonen.
4. Einen Browser (Safari, Chrome, Firefox — egal welcher).
5. Optional: **Claude Code** oder **Codex CLI** als KI-Assistent im Terminal.

## 1. Projekt klonen

```bash
git clone <GITHUB-URL-DIE-PATRICK-DIR-SCHICKT>.git
cd lehr-eval
```

## 2. Abhaengigkeiten installieren

```bash
uv sync
```

`uv` legt automatisch ein virtuelles Python-Environment im Ordner `.venv`
an und installiert alle benoetigten Pakete (FastAPI, openpyxl, qrcode, …).

## 3. Tests laufen lassen (Sanity-Check)

```bash
uv run pytest -q
```

Du solltest am Ende sehen: `121 passed` (oder mehr) und keine Fehler.

## 4. Server lokal starten

```bash
LEHR_EVAL_ADMIN_PASSWORD=secret \
LEHR_EVAL_BASE_URL=http://127.0.0.1:8000 \
uv run uvicorn --app-dir src lehr_eval.app:create_app \
  --factory --reload --host 127.0.0.1 --port 8000
```

Dann oeffne im Browser:

- Admin-Login: <http://127.0.0.1:8000/admin/login> (Passwort: `secret`)
- Health-Check: <http://127.0.0.1:8000/health>

## 5. Erstes Durchspielen

1. **Admin-Login** mit Passwort `secret`.
2. Auf der Seite **„Stammdaten importieren"** waehle die Beispieldatei
   `examples/stammdaten-import.xlsx` (oder die `.csv`-Variante). Beide
   funktionieren.
3. In der Tabelle erscheinen vier vorbereitete Evaluationen.
   Klick bei einer auf **Aktivieren** — Status wird zu `active`.
4. Klick **QR-Material** bei dieser Evaluation. Du bekommst eine
   ZIP-Datei mit Schueler-QR, Lehrkraft-QR und einer kleinen HTML-Seite,
   auf der die Lehrkraft-PIN steht.
5. Oeffne die HTML in der ZIP → dort findest du die **Lehrkraft-PIN**
   und zwei Links: einen fuer die Lehrkraft, einen fuer Schueler.
6. In einem **zweiten Browser-Fenster** (oder Inkognito) oeffnest du den
   **Lehrkraft-Link** und gibst die PIN ein. Du bist jetzt in der
   Live-Steuerung.
7. Klick **Starten** (= Beitrittsphase).
8. In einem **dritten Browser-Fenster** oeffne den **Schueler-Link**.
   Du bekommst einen Tiernamen und siehst „Bitte warten".
9. Zurueck in der Lehrkraft-Ansicht: **Item zeigen** → der Schueler sieht
   jetzt die Frage, aber noch keine Antwortbuttons.
10. **Antworten freigeben** → der Schueler sieht 4 Antworten
    (0 = „stimme nicht zu" … 3 = „stimme zu"). Auswaehlen → **Antwort abgeben**.
    Du siehst „Gespeichert" und kannst nochmal eine andere Antwort waehlen
    → der Button heisst dann „Antwort aendern".
11. Lehrkraft klickt **Naechstes Item** → speichert die Aggregation
    von Item 1 ab und blendet Item 2 ein (gleicher Ablauf).
12. Wenn alle Items durch sind oder du **Schliessen** klickst, ist die
    Evaluation `closed`.
13. Im Admin: **XLSX** herunterladen → du bekommst die Auswertung als Excel.

## 6. Eigene Fragebogen-Texte hinterlegen

Die zwei Fragebogen-Versionen liegen in:

- `examples/fragebogen-unterstufe.md` (Klassenstufen 1–6)
- `examples/fragebogen-oberstufe.md` (Klassenstufen 7–10)

Beide sind ganz normale Markdown-Dateien. Aendere einfach die nummerierte
Liste unter `## Items` (es muessen genau 10 sein). Die Datei wird beim
Server-Start eingelesen — also einfach `Strg-C` und den Server neu starten.

## 7. Eigene Stammdaten importieren

Schau dir `examples/stammdaten-import.csv` an. Die Spalten muessen so heissen:

```
schuljahr, klassenstufe, klasse_lerngruppe, fach,
lehrkraft_name, lehrkraft_kennung, erwartete_teilnehmerzahl
```

Du kannst die Datei direkt in Excel oeffnen, anpassen, als `.xlsx`
speichern und im Admin-UI hochladen — beides geht.

## 8. Wenn etwas haengt

- Server-Logs siehst du in dem Terminal, in dem `uvicorn` laeuft.
- Loescht du `/var/lib/lehr-eval/eval.db` (Linux) oder die lokale
  `.db`-Datei, ist alles wieder zurueckgesetzt.
- Bei UI-Fragen: oeffne im Browser die Entwickler-Konsole (F12), dort
  siehst du SSE-Verbindung und Fehler.

## 9. KI-Assistent benutzen

Wenn du Claude Code oder Codex CLI hast: starte ihn in diesem Ordner
und sag ihm z. B.:

> „Starte den lokalen Lehr-Evaluations-Server und oeffne den Admin-Login
> in meinem Browser."

oder

> „Erkaer mir, wie der Schueler-Antwort-Flow im Code funktioniert."

Die wichtigste Datei zum Verstehen ist `CONTEXT.md` — sie enthaelt die
ganze Fach-Sprache (was eine `Unterrichtsgruppe` ist, was eine `Teilnahme`
ist usw.).

## 10. Produktiv betreiben (optional)

Fuer den Produktiv-Einsatz an einer Schule siehst du in `README.md`
einen Abschnitt **Production Notes** mit:
- HTTPS via Caddy (Beispiel in `ops/Caddyfile.example`)
- systemd-Unit (`ops/lehr-eval.service`)
- Backup-Skript (`ops/backup-sqlite.sh`)

## Architektur in einem Satz

FastAPI + SQLite (WAL), Server-Sent Events fuer Live-Updates der
Lehrkraft-Steuerung und Schueler-Seiten, fertig.

Viel Spass — bei Fragen Patrick anschreiben.
