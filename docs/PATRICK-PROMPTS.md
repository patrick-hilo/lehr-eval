# Patricks Prompts — Aenderungshistorie

Diese Datei dokumentiert die zweite Arbeitsphase an diesem Repo:
nachdem die Initial-Implementation stand (siehe Initial-Commit
mit `agents.md`, `CONTEXT.md`, `README.md` und allen Quelldateien),
hat Patrick das Repo gemeinsam mit Claude Code weiter verbessert.

Die folgenden Eintraege sind die **wortwoertlichen Texte**, die
Patrick in den Chat getippt oder per Sprache eingegeben hat
(inklusive Sprache-zu-Text-Eigenheiten). Pro Eintrag steht
darunter, was umgesetzt wurde.

Damit kannst du nachvollziehen, warum das Repo in seinem heutigen
Zustand so aussieht, wie es aussieht.

---

## 1. Test der Implementation und erste Befunde

> Schau dir das Repo an und ich möchte dass du die aktuelle Implementation auf Herz und Nieren durchtestest.
> Was ich schon gesehen habe, was nicht zu funktionieren scheint, ist:
> - Im Webfrontend werden die Items aus dem Fragebogen gar nicht angezeigt.
> - Wenn man z. B. als Schüler auf eine Antwort klickt und also „Abgeben" anklickt, wird nichts und man reloadet die Seite. Man sieht dann nochmal die gleiche Frage, weil man gerade kein Feedback bekommt, dass man es eingegeben hat.
> Außerdem war in der Spezifikation danach, dass man die Antwort noch ändern kann. Das heißt, das Frontend muss entsprechend noch ein bisschen angepasst werden.
> Schau dir den aktuellen Projektstand an und dann lass uns gemeinsam diskutieren, wie wir den Projektstand noch ein bisschen verbessern können

**Ergebnis:** Analyse + Befunde dokumentiert. Identifizierte Probleme:
Fragebogen enthielt nur Platzhalter `Item 1`…`Item 10`, Antwort-Submit
zeigte kein Feedback und keine Vorauswahl, Antwort war nicht
nachtraeglich aenderbar (obwohl Spec das verlangt).

---

## 2. Zwei Fragebögen, Markdown-Loader, XLSX-Support, durchtesten, änderbare Antworten

> Denk dir mal zwei unterschiedliche Fragebögen aus und erweitere das System so, dass du die Fragebögen als Markter direkt in dem Example-Ordner einlesen kannst. Das heißt, ich kann dann quasi einfach die Fragebögen auch mit hochladen, die ganzen Modifikationen setzen, den lokalen Server starten und Page and Browser durchtesten.
>
> Bevor du das machst, füge bitte gleich noch Excel-Support hinzu. Das sollte in Python keine große Magie sein, sodass der Nutzer anstatt einer CSV-Datei eine Excel-Datei hochlegt und auch eine Excel-Datei darunter geladen bekommt. Dann teste das ganze System auf Herz und Nieren durch, bis es wirklich gut funktioniert, und lass den Nutzer auch zwischendurch eine Antwort verändern können

**Ergebnis:**
- `examples/fragebogen-unterstufe.md` und `examples/fragebogen-oberstufe.md` mit je 10 Items, beim Server-Start ueber `questionnaires.py` eingelesen.
- XLSX-Upload zusaetzlich zur CSV (openpyxl, `examples/stammdaten-import.xlsx`).
- Schueler-UI: vorausgewaehlte Antwort, „Gespeichert"-Bestaetigung, Button-Label „Antwort aendern".
- End-to-End durchgetestet (Admin-Login -> XLSX-Import -> Aktivieren -> Lehrkraft -> Beitritt -> Frage zeigen -> Antworten freigeben -> Antwort abgeben -> aendern -> Naechstes Item -> Schliessen -> XLSX-Export).

---

## 3. Public Repo + Handoff fuer einen Freund (Folgeauftrag direkt nach 2)

> anschließend erstelle ein private repo auf github und committe den stand da rein.
>
> Dann erstelle ich eine Hand-off-Datei. Die ermöglicht es ihm, auf einem anderen Computer ohne die ganzen Kontakten, die wir beide haben, an dem Projekt aktiv weiterzuarbeiten. Es erklärt ihm ganz einfach, was er tun muss, um das Projekt aufzusetzen, sodass mein Freund, der nicht so affin ist, auf seinem anderen Rechner dann das gesamte Setup auch laufen kriegt, obwohl er nur Codecs da drauflaufen hat oder Claude Code

**Ergebnis:** HANDOFF.md geschrieben (Setup-Schritte, Voraussetzungen, Erstes Durchspielen, eigene Fragebogen-Texte hinterlegen, Produktiv-Hinweise). Private Repo zunaechst geplant (spaeter durch Eintrag 9 in „public" geaendert).

---

## 4. Frontend-Design

> Bitte mach noch ein tolles Design für das frontend

**Ergebnis:** Neues Design-System: ruhiges Schul-Look (Indigo-Akzent, Karten-Layout), Status-Pills, Live-Status-Karte mit Gradient, Tablet-/Mobile-taugliche Schueler-Sicht mit grossen Touch-Targets, Inter-Webfont, ausgegraute Disabled-Zustaende.

---

## 5. Einfache Sprache fuer die Fragebogen

> Lassen Sie Fragebögen in einfacher Sprache formulieren.

**Ergebnis:** Unter- und Oberstufen-Fragebogen in Einfacher Sprache umformuliert (kurze Saetze, „Ich"-Form, vertraute Worte, klare Skala 0–3).

---

## 6. Schritt 0 fuer den Coding-Agent in HANDOFF

> Füge im Handoff eine Section zu, dass der erste Schritt eh eh sein sollte für den Code -- nächsten Coding Agent, der sich das ganze repo anschaut. Alles auf dem Rechner zu installieren, was notwendig ist, um dieses repo zu starten. Das repo zu starten, die Webseite zu öffnen vom Admin Panel und dem Nutzer zu sagen, das Passwort ist secret, sodass er dann quasi sich direkt einloggen kann. Und es selber auf seinem Rechner ausprobieren kann.

**Ergebnis:** „Schritt 0 — Fuer den KI-Coding-Agent" am Anfang von HANDOFF.md: clone → `uv sync` → Server starten → Admin-Login oeffnen → Nutzer das Passwort `secret` mitteilen.

---

## 7. QR-Material-Download funktioniert nicht

> Der Download des QR-Materials scheint nicht zu funktionieren. Im Browser wird zwar angezeigt, dass was heruntergeladen wird, aber es ist keine Datei

**Ergebnis:** Backend war korrekt (200 + `application/zip` + `Content-Disposition: attachment`), aber Link wurde robuster gemacht: neuer Endpoint `/admin/evaluations/{id}/qr-material.zip` (URL endet auf `.zip`), Anchor bekam `download="qr-material-{id}.zip"`.

---

## 8. Bulk-Actions und Status-Filter im Admin

> Lass uns im Admin-Panel noch Bulk Actions hinzufügen, sodass ich oben ein Häkchen setzen kann. Da werden alle Zeilen markiert und ich kann dann alle auf einmal eine bestimmte Aktion durchführen lassen, sodass ich das nicht manuell mit jeder einzelnen machen muss.
> Lass uns in dem Admin-Panel auch einen Filter hinzufügen, sodass ich filtern kann auf:
> - aktive
> - nicht aktive
> - so weiter
> nach dem Status. Dann kann ich mit zwei Aktionen nämlich:
> 1. Filter auf aktive
> 2. Bulk Action mit der Bulk Action deaktivieren und alle auf einmal deaktivieren
>
> Löse alle die Befunde, die du noch hast

**Ergebnis:** Filter-Chips ueber der Tabelle (mit Counts je Status), Checkbox-Spalte + Select-all-Master, Bulk-Bar mit Aktivieren / Deaktivieren / Loeschen. Backend-Endpoint `/admin/evaluations/bulk`. Zusatzbefunde geloest: persistenter `secret_key` (Sessions ueberleben Restart), QR-Anchor-Fix, Disabled-Buttons fuer ungueltige Lehrer-Aktionen.

---

## 9. Public Repo + Freund braucht keinen GitHub-Account

> Committe das GitHub-Repo zu GitHub und passe entsprechend das Hand-Off an. Macht das GitHub-Repo public sodass er keinen GitHub-Account dafür anlegen muss

**Ergebnis:** Repo erstellt unter <https://github.com/patrick-hilo/lehr-eval>, sichtbar als **public**. HANDOFF.md mit dieser URL aktualisiert, Hinweis „kein GitHub-Account noetig" ergaenzt.

---

## 10. Reicht es, dem Freund die Markdown-Datei zu schicken?

> Dann reicht es für dich, dass ich denen, ist mein Freund, die Hand auf die Marktdaten schicken und die sage: „So sind ein Ordner packen" und dann macht Kodex den Rest für ihn richtig?

**Ergebnis:** Erklaerung: noch einfacher — dem Freund nur die GitHub-URL schicken; Codex / Claude Code wird dann angewiesen, „lies HANDOFF.md und arbeite Schritt 0 durch". Damit clone + uv sync + Server + Admin-Login + Passwort-Hinweis automatisch.

---

## 11. „$ entire enable"

> $ entire enable

**Ergebnis:** Lokales Tool-Kommando — habe nachgefragt, ob das wirklich ausgefuehrt werden soll.

---

## 12. Ja bitte

> ja bitte

**Ergebnis:** `entire enable` ausgefuehrt — installierte Claude-Code-Search-Subagent + Hooks + `.entire/settings.json`.

---

## 13. Entire-Konfig bleibt lokal

> bleiben lokal

**Ergebnis:** `.claude/` und `.entire/` in `.gitignore` aufgenommen, damit die persoenliche Tool-Konfig nicht ins Repo wandert.

---

## 14. start.sh

> adde mal noch ein script wie start.sh das den Webserver startet und das Admin panel aufruft und leg das script in das repo

**Ergebnis:** `start.sh` geschrieben — checked `uv`, syncht Abhaengigkeiten, startet uvicorn, wartet auf `/health`, schreibt PID-Datei, oeffnet Admin-Login im Browser (macOS `open`, Linux/WSL `xdg-open`).

---

## 15. stop.sh

> und dann noch ein script für stop was alles wieder stopt

**Ergebnis:** `stop.sh` schreibt SIGTERM an die PID aus `.lehr-eval.pid`, fallback `pkill` fuer verwaiste lehr_eval-uvicorn-Prozesse.

---

## 16. WSL-Frage

> neues git commit und handoff.md anpassen mit den infos dazu - funktionieren die scripte auch auf widnows in der WSL?

**Ergebnis:** Bestaetigt: ja, WSL2 mit WSLg oeffnet den Browser; ohne WSLg druckt das Script die URL. `.gitattributes` erzwingt LF-Zeilenenden, damit Bash-Scripts unter Windows-Git nicht mit CRLF beschaedigt werden. HANDOFF mit Plattform-Hinweisen ergaenzt.

---

## 17. start.sh oeffnet das Admin-Panel nicht

> ./start.sh
> → Installiere Abhaengigkeiten via 'uv sync'...
> → Starte Server auf http://127.0.0.1:8000/admin/login...
>
> öffnet bei mir gerade nicht das admin panel?

**Ergebnis:** Diagnose: ein frueher manuell gestarteter uvicorn lief noch auf Port 8000; mein neuer Server konnte sich nicht binden. start.sh raeumt jetzt verwaiste lehr_eval-uvicorn-Prozesse vor dem Start ab, prueft den Port und gibt sonst eine klare Fehlermeldung mit `LEHR_EVAL_PORT=...`-Hinweis.

---

## 18. Bitte committen

> bitte commiten

**Ergebnis:** start.sh-Fix committed + gepusht.

---

## 19. Failure-Mode verhindern: ausgegraute Lehrer-Buttons

> Aktuell wenn man als Lehrer auf „Starten" drückt, obwohl das System gerade aktiv ist, kommt ein Command. So etwas sollte eigentlich nicht passieren. Bitte stell sicher dass in jedem Status alles, was der Lehrer und der Schüler klicken kann, nicht dazu führt, dass da quasi ein Failure-Mode kommt. Wenn der „Starten"-Button keinen Sinn macht wie in dem Fall, in dem der Status gerade aktiv ist, dann bitte ich dich, diesen Status auszugrauen

**Ergebnis:** Lehrer-Template berechnet pro Phase eine Whitelist erlaubter Aktionen; nicht erlaubte Buttons sind `disabled` + ausgegraut. Phase-Hinweis-Zeile fuehrt durch den naechsten Schritt. Backend redirected ungueltige Aktionen statt 409 JSON zu liefern (doppelte Absicherung). Schueler-Endpoint analog.

---

## 20. „Item" → „Frage" im Frontend

> Lass uns das Wort item durchfrage in dem Frontend für Lehrer und Schüler ersetzen. Das ist nicht so nett. Wenn alles durch grün läuft, bitte noch mal ein GitHub commit und Push mitmachen und die Handoff Datei falls notwendig anpassen.

**Ergebnis:** Lehrer-Live: „Frage zeigen", „Naechste Frage", „Aktuelle Frage", Phase-Hinweise umformuliert. DB-Keys (`Item 1`…`Item 10`) bleiben stabil, damit Exports kompatibel sind.

---

## 21. Funktionieren Bulk Actions und Status-Filter?

> Funktionieren die Bulk actions im admin Panel und die Status Filter?

**Ergebnis:** End-to-End-Verifikation: Filter-Chips zeigen Counts, `?status=prepared` filtert, Bulk-Activate auf 4 Zeilen, Bulk-Deactivate aus Filter-Kontext (leitet auf `?status=active` zurueck), Bulk-Delete nur fuer ungenutzte Evaluationen.

---

## 22. Diese Datei

> Ich möchte, dass mein Freund nachvollziehen kann, was ich alles getan habe. Das heißt, kauft ihr unsere gesamte Konversation an? und nehme die Texte, die ich reingegeben habe, verkürzt, verknappt, sodass man, nee, genau die Texte ich reingegeben habe, Werbeteam, immer quasi als, das ist Patricks Input, eins, zwei, drei, vier, was auch immer. Wenn der gesamten Konversation erstelle auch aus 'nem Background Datei, packt die in das repo, committed die. Und im Handoff schreibt rein son Kommentar, also soll der Nutzer son Kommentar sehen, wenn das Handoff durchgeführt durch Kodex oder Claude. Hier, das ist das all das, was Patrick noch nachträglich gemacht hat.

**Ergebnis:** Diese Datei (`docs/PATRICK-PROMPTS.md`) angelegt — wortwoertliche Patrick-Prompts in chronologischer Reihenfolge, jeder mit kurzem Ergebnis-Vermerk. HANDOFF zeigt einen Hinweis-Block, der den Coding-Agent auffordert, den Nutzer auf diese Datei aufmerksam zu machen.
