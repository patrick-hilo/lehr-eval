# Lehr-Evaluation

Dieser Kontext beschreibt die fachlichen Begriffe fuer schulische Unterrichtsevaluationen am Ende eines Schuljahres.

## Language

**Unterrichtsgruppe**:
Eine konkrete Kombination aus Schuljahr, Klasse oder Lerngruppe, Fach und Lehrkraft.
_Avoid_: Kurs

**Evaluation**:
Eine Umfrage zu einer Unterrichtsgruppe, die Schueler am Ende eines Schuljahres beantworten.
_Avoid_: Umfrage, Befragung

**Vorbereitete Evaluation**:
Eine importierte Evaluation, deren QR-Codes noch nicht fuer die Durchfuehrung aktiv sind.
_Avoid_: Entwurf

**Aktivierte Evaluation**:
Eine vorbereitete Evaluation, deren QR-Codes durch die Administration fuer die Durchfuehrung freigeschaltet wurden.
_Avoid_: Freigeschaltete Umfrage

**Deaktivierte Evaluation**:
Eine zuvor aktivierte Evaluation, deren QR-Codes vor dem ersten Beitritt oder Start wieder unwirksam gemacht wurden.
_Avoid_: Geloeschte Evaluation

**Ungenutzte Evaluation**:
Eine vorbereitete oder deaktivierte Evaluation ohne Beitritte, Antworten oder festgeschriebene Items.
_Avoid_: Leere Evaluation

**Korrekturimport**:
Ein erneuter Stammdatenimport nach Entfernen ungenutzter fehlerhafter Evaluationen.
_Avoid_: Nachtraegliches Aendern laufender Evaluationen

**Geschlossene Evaluation**:
Eine Evaluation, die durch die Lehrkraft endgueltig beendet wurde und keine weiteren Beitritte, Wiederbeitritte oder Antworten mehr erlaubt.
_Avoid_: Abgeschlossene Umfrage, Archiv

**Live-Daten**:
Die nur waehrend einer laufenden Evaluation benoetigten Daten zu Teilnahmen, Tiernamen, Verbindungen und aktuellen Item-Antworten.
_Avoid_: Rohdaten, Antwortprofil

**Pausierte Evaluation**:
Eine laufende Evaluation, die nicht beendet ist und zu einem spaeteren Zeitpunkt ueber dieselben QR-Codes fortgesetzt werden kann.
_Avoid_: Abgebrochene Evaluation

**Pruefbeduerftige Evaluation**:
Eine pausierte Evaluation, die seit 14 Tagen nicht geschlossen wurde und eine administrative Entscheidung erfordert.
_Avoid_: Automatisch abgelaufene Evaluation

**Beitrittsphase**:
Die Phase vor dem Start des ersten Items, in der neue Teilnahmen einer Evaluation beitreten koennen.
_Avoid_: Registrierung, Anmeldung

**Start trotz fehlender Beitritte**:
Eine bewusste Entscheidung der Lehrkraft, die Evaluation zu starten, obwohl weniger Teilnahmen beigetreten sind als erwartet.
_Avoid_: Automatischer Start

**Lehrkraft-PIN**:
Ein vierstelliger Code einer Lehrkraft fuer ein Schuljahr, der zusammen mit einem Lehrkraft-QR den Zugriff auf die Live-Steuerung eigener Evaluationen erlaubt, aber keinen Ergebniszugriff gibt.
_Avoid_: Passwort, Login

**PIN-Fehlversuch**:
Eine falsche Eingabe der Lehrkraft-PIN beim Oeffnen der Live-Steuerung, die verzoegert oder begrenzt werden kann ohne die Evaluation zu sperren.
_Avoid_: Kontosperre

**PIN-Rotation**:
Das administrative Neuerzeugen einer Lehrkraft-PIN, wodurch die vorherige PIN ungueltig wird.
_Avoid_: PIN-Aenderung durch Lehrkraft

**Freigegebene Ergebnisse**:
Aggregationsergebnisse einer geschlossenen Evaluation, die durch die Administration fuer eine Weitergabe ausserhalb des Evaluationssystems freigegeben wurden.
_Avoid_: Live-Ergebnisse, automatische Ergebnisfreigabe, Lehrkraft-Portal

**Aggregation**:
Eine zusammengefasste Auswertung je Item mit Verteilung, Mittelwert und Antwortanzahlen ohne einzelne Antwortdatensaetze.
_Avoid_: Rohdaten, Einzeldaten, Antwortliste

**Item-Aggregat**:
Die dauerhaft gespeicherte Zusammenfassung eines Items mit Antwortwert-Zaehlungen, fehlenden Antworten, beigetretenen Teilnahmen und Mittelwert.
_Avoid_: Rohdaten, Antwortereignis, Einzelantwort

**Aufbewahrungsfrist**:
Der Zeitraum von drei Schuljahren, fuer den Item-Aggregate nach Abschluss gespeichert bleiben.
_Avoid_: Dauerhafte Speicherung

**Loeschlauf**:
Das bewusste administrative Entfernen von Item-Aggregaten, deren Aufbewahrungsfrist abgelaufen ist.
_Avoid_: Automatische Loeschung

**Einzel-Export**:
Eine einfache Excel-Auswertung ohne Diagramme fuer genau eine Evaluation.
_Avoid_: Einzelbericht

**Export-Kopfzeile**:
Die Metadaten eines Einzel-Exports mit Schuljahr, Unterrichtsgruppe, Fragebogen-Version, Teilnehmerzahlen, Abschlussdatum und Aggregationshinweis.
_Avoid_: Deckblatt

**Export-Blattname**:
Der Excel-Tabellenblattname einer Evaluation, gebildet aus Klasse oder Lerngruppe und Fach, bei Kollisionen nummeriert.
_Avoid_: Technischer Blattname

**Lehrkraft-Export**:
Eine einfache Excel-Auswertung mit einem Blatt pro Evaluation im Einzel-Export-Format, ohne zusaetzliche Uebersichtsseite.
_Avoid_: Sammel-Export

**Exportfunktion**:
Eine administrative Funktion zur Erzeugung einfacher Excel-Dateien fuer die externe Weitergabe an Lehrkraefte.
_Avoid_: Auswertungsoberflaeche, Dashboard, Diagramm

**Systemsprache**:
Die Sprache der Oberflaechen, Frageboegen und Exporte im ersten Scope.
_Avoid_: Mehrsprachigkeit

**Festgeschriebenes Item**:
Ein Item, dessen Item-Aggregat durch das Fortfahren der Lehrkraft fixiert wurde.
_Avoid_: Abgeschlossene Frage

**Fragebogen**:
Ein fester Katalog von Items fuer eine Stufe, der ueber Lehrkraefte, Klassen und Faecher hinweg identisch ist.
_Avoid_: Fragenliste, Item-Set

**Fragebogen-Version**:
Die fuer eine Evaluation gueltige Fassung eines Fragebogens.
_Avoid_: Aktuelle Fragen

**Unterstufen-Fragebogen**:
Der feste Fragebogen fuer Evaluationen in den Klassenstufen 1 bis 6.
_Avoid_: Unterstufenfragen

**Oberstufen-Fragebogen**:
Der feste Fragebogen fuer Evaluationen in den Klassenstufen 7 bis 10.
_Avoid_: Oberstufenfragen

**Administration**:
Die Rolle, die Evaluationen vorbereitet und Zugriff auf alle Evaluationen hat.
_Avoid_: Direktor, Admin, Verwaltung

**Admin-Protokoll**:
Eine Nachvollziehbarkeit administrativer Aktionen ohne dauerhafte Protokollierung von Schueler- oder Antwortaktionen.
_Avoid_: Schuelerprotokoll, Antwortprotokoll

**Stammdatenimport**:
Das Einlesen vorbereiteter Schuljahres-, Klassen-, Fach-, Lehrkraft- und Unterrichtsgruppendaten durch die Administration, um Evaluationen und QR-Material vorzubereiten.
_Avoid_: Manuelle Pflege, Einzelerfassung

**Importspalte**:
Eine verpflichtende Spalte im Stammdatenimport fuer Schuljahr, Klassenstufe, Klasse oder Lerngruppe, Fach, Lehrkraft-Anzeigename, Lehrkraft-Kennung und erwartete Teilnehmerzahl.
_Avoid_: Freies Feld

**Lehrkraft-Kennung**:
Die eindeutige Kennung einer Lehrkraft im Stammdatenimport, bevorzugt die schulische E-Mail-Adresse.
_Avoid_: Nur Anzeigename

**Importfehler**:
Ein Validierungsproblem im Stammdatenimport, das den gesamten Import verhindert.
_Avoid_: Teilimport

**Doppelte Unterrichtsgruppe**:
Eine Importzeile, deren Kombination aus Schuljahr, Klasse oder Lerngruppe, Fach und Lehrkraft-Kennung bereits als Evaluation existiert.
_Avoid_: Zweite Evaluation

**Erwartete Teilnehmerzahl**:
Die im Stammdatenimport angegebene Anzahl der voraussichtlich teilnehmenden Schueler einer Unterrichtsgruppe.
_Avoid_: Klassengroesse, Soll-Teilnehmer

**QR-Material**:
Die fuer eine Evaluation erzeugten druckbaren Zugangsunterlagen mit Schueler-QR, Lehrkraft-QR und zugeordneter Lehrkraft-PIN.
_Avoid_: Linkliste

**Schueler-QR**:
Der QR-Code einer Evaluation, der in den anonymen Teilnahmefluss fuehrt.
_Avoid_: Teilnahme-Link

**Lehrkraft-QR**:
Der QR-Code einer Evaluation, der mit Lehrkraft-PIN in die Live-Steuerung fuehrt.
_Avoid_: Steuerungs-Link

**Lehrkraft**:
Die Rolle, die eine vorbereitete Evaluation live durchfuehrt und eigene Ergebnisse aggregiert einsehen darf.
_Avoid_: Lehrer

**Teilnahme**:
Eine anonyme Live-Bearbeitung einer Evaluation durch einen Schueler, ohne gespeicherte reale Schueleridentitaet und ohne dauerhaftes Antwortprofil.
_Avoid_: Schueler, Schueleraccount, Antwortperson

**Wiederbeitrittscode**:
Ein waehrend einer laufenden Evaluation vergebener anonymer Merker, mit dem eine Teilnahme nach einem technischen Abbruch fortgesetzt und von der Lehrkraft im Live-Fortschritt erkannt werden kann.
_Avoid_: Login, Benutzername, Passwort, Identitaetsnachweis

**Wiederbeitritt**:
Das Fortsetzen einer bestehenden Teilnahme nach einem technischen Abbruch, automatisch auf demselben Geraet oder manuell ueber den Tiernamen.
_Avoid_: Neuer Beitritt, Login

**Tiername**:
Ein innerhalb einer laufenden Evaluation eindeutiger Wiederbeitrittscode fuer genau eine Teilnahme.
_Avoid_: Teilnehmername, Spitzname

**Erweiterter Tiername**:
Ein Wiederbeitrittscode aus neutralem oder positivem Adjektiv und Tiername, der verwendet wird, wenn einfache Tiernamen fuer die erwartete Teilnehmerzahl nicht ausreichen.
_Avoid_: Doppelter Tiername

**Live-Status**:
Der waehrend einer laufenden Evaluation sichtbare Fortschritt einer Teilnahme ohne sichtbaren Antwortinhalt.
_Avoid_: Antwortuebersicht, Ergebnisstatus

**Lesephase**:
Die Phase eines Items, in der Schueler das Item sehen, aber noch keine Antwort abgeben koennen.
_Avoid_: Fragevorschau

**Antwortphase**:
Die Phase eines Items, in der Schueler die Antwortoptionen sehen und ihren Antwortwert bis zum Beenden der Phase aendern koennen.
_Avoid_: Abstimmung

**Item-Antwort**:
Die zuletzt gewaehlte Bewertung einer Teilnahme zu einem Item innerhalb einer laufenden Evaluation, die nicht dauerhaft mit anderen Antworten derselben Teilnahme verbunden wird.
_Avoid_: Antwortbogen, Antwortserie, Profil

**Antwortwert**:
Der numerische Wert einer Item-Antwort auf einer Skala von 0 fuer "stimme nicht zu" bis 3 fuer "stimme zu".
_Avoid_: Punktzahl, Note

**Fehlende Antwort**:
Ein nicht abgegebener Antwortwert zu einem Item aufgrund eines technischen Abbruchs oder Nicht-Fortsetzens einer Teilnahme.
_Avoid_: Enthaltung, Ueberspringen, keine Angabe

**Fortfahren trotz fehlender Antworten**:
Eine bewusste Entscheidung der Lehrkraft, eine Evaluation fortzusetzen, obwohl nicht alle Teilnahmen das aktuelle Item beantwortet haben.
_Avoid_: Automatisches Ueberspringen

## Relationships

- Eine **Evaluation** gehoert genau zu einer **Unterrichtsgruppe**.
- Eine **Evaluation** verwendet genau einen **Fragebogen**.
- Eine **Evaluation** behaelt ihre **Fragebogen-Version**.
- Der **Fragebogen** einer **Evaluation** ergibt sich aus der Klassenstufe der **Unterrichtsgruppe**.
- Eine **Unterrichtsgruppe** kann pro Schuljahr eine **Evaluation** haben.
- Eine **Doppelte Unterrichtsgruppe** ist ein **Importfehler**.
- Eine **Unterrichtsgruppe** hat eine **Erwartete Teilnehmerzahl**.
- Die **Administration** bereitet **Unterrichtsgruppen** ueber einen **Stammdatenimport** vor.
- Ein **Stammdatenimport** enthaelt verpflichtende **Importspalten**.
- Ein **Stammdatenimport** wird nur vollstaendig uebernommen, wenn keine **Importfehler** vorliegen.
- Ein **Stammdatenimport** erzeugt **Vorbereitete Evaluationen** und **QR-Material**.
- Die **Administration** kann **Vorbereitete Evaluationen** zu **Aktivierten Evaluationen** machen.
- Die **Administration** kann eine **Aktivierte Evaluation** vor dem ersten Beitritt oder Start zu einer **Deaktivierten Evaluation** machen.
- Die **Administration** kann nur **Ungenutzte Evaluationen** loeschen.
- Ein **Korrekturimport** ist nur vor Nutzung der betroffenen **Evaluationen** moeglich.
- Die **Administration** erstellt **Evaluationen** ueber den **Stammdatenimport**.
- Das **QR-Material** einer **Evaluation** enthaelt genau einen **Schueler-QR** und genau einen **Lehrkraft-QR**.
- Eine **Lehrkraft** fuehrt vorbereitete **Evaluationen** live durch.
- Eine **Lehrkraft** hat pro Schuljahr genau eine **Lehrkraft-PIN**.
- Die **Lehrkraft-PIN** wird automatisch erzeugt.
- Die **Administration** kann eine **PIN-Rotation** fuer eine **Lehrkraft-PIN** ausloesen.
- Die **Lehrkraft-Kennung** wird nur intern verwendet und erscheint nicht in **QR-Material** oder Exporten.
- Eine **Lehrkraft** oeffnet die Live-Steuerung einer eigenen **Evaluation** mit Lehrkraft-QR und **Lehrkraft-PIN**.
- Eine **Lehrkraft** kann die Live-Steuerung einer laufenden oder **Pausierten Evaluation** mit Lehrkraft-QR und **Lehrkraft-PIN** wieder aufnehmen.
- Eine **Evaluation** kann durch die Lehrkraft zu einer **Geschlossenen Evaluation** werden.
- Beim Schliessen einer **Evaluation** werden **Live-Daten** geloescht oder von **Item-Aggregaten** entkoppelt.
- Eine **Evaluation** kann als **Pausierte Evaluation** ueber dieselben QR-Codes fortgesetzt werden.
- Eine **Pausierte Evaluation** wird nach 14 Tagen zu einer **Pruefbeduerftigen Evaluation**.
- Neue **Teilnahmen** koennen nur waehrend der **Beitrittsphase** entstehen.
- Nach der **Beitrittsphase** koennen nur bestehende **Teilnahmen** ueber ihren **Wiederbeitrittscode** zurueckkehren.
- Ein **Wiederbeitritt** kann automatisch auf demselben Geraet oder manuell ueber den **Tiernamen** erfolgen.
- Ein **Wiederbeitritt** auf einem neuen Geraet ersetzt die vorherige aktive Verbindung derselben **Teilnahme**.
- Eine Lehrkraft kann **Start trotz fehlender Beitritte** ausloesen.
- Die **Administration** kann laufende oder **Pausierte Evaluationen** administrativ schliessen.
- Die **Administration** kann Ergebnisse einer **Geschlossenen Evaluation** als **Freigegebene Ergebnisse** fuer externe Weitergabe markieren.
- Administrative Aktionen werden im **Admin-Protokoll** festgehalten.
- Das **Admin-Protokoll** unterliegt einer **Aufbewahrungsfrist** von drei Schuljahren.
- Schueler- und Antwortaktionen werden nicht dauerhaft protokolliert.
- Eine **Lehrkraft** kann nach Freigabe nur **Aggregationen** sehen.
- Die **Administration** kann einen **Einzel-Export** fuer eine **Evaluation** erzeugen.
- Ein **Einzel-Export** enthaelt eine **Export-Kopfzeile**.
- Die **Administration** kann einen **Lehrkraft-Export** fuer mehrere **Evaluationen** einer **Lehrkraft** erzeugen.
- Im **Lehrkraft-Export** verwendet jedes Blatt einen **Export-Blattnamen**.
- Das Evaluationssystem stellt **Exportfunktionen** bereit, aber keine Ergebnis-Dashboards oder grafischen Auswertungen.
- **Exportfunktionen** enthalten **Item-Aggregate** einschliesslich Antwortwert-Zaehlungen, fehlenden Antworten, beigetretenen Teilnahmen und Mittelwert.
- **Exportfunktionen** zeigen **Erwartete Teilnehmerzahl** und tatsaechlich beigetretene **Teilnahmen** getrennt.
- Excel-Exporte werden bei Bedarf aus **Item-Aggregaten** erzeugt und nicht dauerhaft im Evaluationssystem gespeichert.
- Die **Systemsprache** ist im ersten Scope Deutsch.
- **Frageboegen** sind im ersten Scope nicht durch die **Administration** editierbar.
- Eine **Lehrkraft** kann die **Erwartete Teilnehmerzahl** nicht aendern.
- Eine **Evaluation** hat mehrere **Teilnahmen**.
- Eine **Teilnahme** gehoert genau zu einer **Evaluation**.
- Eine **Teilnahme** kann waehrend einer laufenden **Evaluation** ueber genau einen **Wiederbeitrittscode** fortgesetzt werden.
- Eine **Teilnahme** hat waehrend einer laufenden **Evaluation** genau einen **Tiernamen**.
- Der **Tiername** einer **Teilnahme** wird beim Beitritt automatisch vergeben.
- Ein **Tiername** wird innerhalb einer **Evaluation** nur einmal vergeben.
- Wenn einfache **Tiernamen** nicht ausreichen, koennen **Erweiterte Tiernamen** vergeben werden.
- Eine Lehrkraft kann **Wiederbeitrittscodes** waehrend einer laufenden **Evaluation** sehen.
- Eine Lehrkraft kann den **Live-Status** je **Wiederbeitrittscode** sehen, aber nicht den Antwortinhalt.
- Jedes Item einer laufenden **Evaluation** durchlaeuft eine **Lesephase** und danach eine **Antwortphase**.
- Eine **Evaluation** hat mehrere **Item-Antworten**.
- Eine **Item-Antwort** gehoert genau zu einem Item einer **Evaluation**.
- Eine **Item-Antwort** hat genau einen **Antwortwert**.
- Bei mehrfacher Aenderung einer **Item-Antwort** zaehlt nur der zuletzt gewaehlte **Antwortwert**.
- Eine **Fehlende Antwort** ist keine **Item-Antwort**.
- Eine Lehrkraft kann **Fortfahren trotz fehlender Antworten** ausloesen.
- Eine **Geschlossene Evaluation** hat dauerhaft gespeicherte **Item-Aggregate**.
- Ein **Item-Aggregat** enthaelt keine einzelnen Antwortereignisse.
- **Item-Aggregate** unterliegen einer **Aufbewahrungsfrist** von drei Schuljahren.
- Nach Ablauf der **Aufbewahrungsfrist** werden **Item-Aggregate** fuer einen administrativen **Loeschlauf** markiert.
- Ein **Festgeschriebenes Item** hat genau ein unveraenderliches **Item-Aggregat**.

## Example dialogue

> **Dev:** "Startet Frau Mueller fuer Klasse 8b Mathematik eine Evaluation?"
> **Domain expert:** "Ja, das ist die Evaluation fuer die Unterrichtsgruppe 2025/26, Klasse 8b, Mathematik, Frau Mueller."
> **Dev:** "Speichern wir, welcher Schueler welche Antworten gegeben hat?"
> **Domain expert:** "Nein, wir speichern nur anonyme Teilnahmen."
> **Dev:** "Kann man spaeter alle Antworten einer Teilnahme zusammen ansehen?"
> **Domain expert:** "Nein, Antworten werden nicht als Antwortserie gespeichert."
> **Dev:** "Was passiert, wenn ein Tablet abstuerzt?"
> **Domain expert:** "Der Schueler nutzt seinen Wiederbeitrittscode und setzt die laufende Teilnahme fort."
> **Dev:** "Kann es in einer Evaluation zweimal denselben Tiernamen geben?"
> **Domain expert:** "Nein, jeder Tiername wird innerhalb einer Evaluation nur einmal vergeben."
> **Dev:** "Was passiert bei mehr als 40 Teilnahmen?"
> **Domain expert:** "Dann werden Tiernamen mit Adjektiven erweitert, damit die Wiederbeitrittscodes eindeutig bleiben."
> **Dev:** "Duerfen Adjektive wie faul verwendet werden?"
> **Domain expert:** "Nein, Adjektive fuer erweiterte Tiernamen sollen neutral oder positiv sein."
> **Dev:** "Sucht der Schueler seinen Tiernamen selbst aus?"
> **Domain expert:** "Nein, der Tiername wird automatisch vergeben."
> **Dev:** "Muss ein Schueler nach einem Reload immer den Tiernamen eingeben?"
> **Domain expert:** "Nein, Wiederbeitritt kann automatisch erfolgen, wenn das Geraet die Teilnahme noch kennt."
> **Dev:** "Ist der Tiername ein starker Identitaetsnachweis?"
> **Domain expert:** "Nein, er ist ein pragmatischer Wiederbeitrittscode fuer die beaufsichtigte Durchfuehrung."
> **Dev:** "Kann derselbe Tiername gleichzeitig auf zwei Geraeten aktiv sein?"
> **Domain expert:** "Nein, ein Wiederbeitritt ersetzt die vorherige aktive Verbindung."
> **Dev:** "Darf die Lehrkraft sehen, welcher Wiederbeitrittscode gerade fehlt?"
> **Domain expert:** "Ja, damit sie warten kann, bis diese Teilnahme wieder verbunden ist."
> **Dev:** "Darf die Lehrkraft sehen, was Waschbaer geantwortet hat?"
> **Domain expert:** "Nein, sie sieht nur den Live-Status, nicht den Antwortinhalt."
> **Dev:** "Kann nach dem Beenden noch jemand ueber den QR-Code antworten?"
> **Domain expert:** "Nein, dann ist die Evaluation geschlossen."
> **Dev:** "Wer legt die Evaluation fuer Frau Mueller an?"
> **Domain expert:** "Die Administration; Frau Mueller fuehrt sie nur durch."
> **Dev:** "Hat Mathematik bei Frau Mueller andere Items als Deutsch bei Herrn Schmidt?"
> **Domain expert:** "Nein, entscheidend ist nur, ob die Evaluation den Unterstufen- oder Oberstufen-Fragebogen nutzt."
> **Dev:** "Welche Klassen nutzen den Oberstufen-Fragebogen?"
> **Domain expert:** "Die Klassenstufen 7 bis 10; Klassenstufen 1 bis 6 nutzen den Unterstufen-Fragebogen."
> **Dev:** "Ist ein hoeherer Mittelwert besser?"
> **Domain expert:** "Ja, 0 bedeutet stimme nicht zu und 3 bedeutet stimme zu."
> **Dev:** "Kann ein Schueler eine Frage ueberspringen?"
> **Domain expert:** "Nein, fehlende Antworten entstehen nur durch technische Abbrueche oder Nicht-Fortsetzen."
> **Dev:** "Muss die Klasse warten, wenn ein Tablet nicht mehr funktioniert?"
> **Domain expert:** "Nein, die Lehrkraft kann bewusst trotz fehlender Antworten fortfahren."
> **Dev:** "Sieht die Lehrkraft direkt nach dem Beenden die Ergebnisse?"
> **Domain expert:** "Nein, erst wenn die Administration die Ergebnisse freigibt."
> **Dev:** "Verschickt das Evaluationssystem Ergebnisse an Lehrkraefte?"
> **Domain expert:** "Nein, die Administration uebermittelt Auswertungen ueber andere Systeme."
> **Dev:** "Welche Exportpakete braucht die Administration?"
> **Domain expert:** "Einzel-Exporte pro Evaluation und Lehrkraft-Exporte ueber mehrere Evaluationen derselben Lehrkraft."
> **Dev:** "Ist der Lehrkraft-Export eine Gesamtbewertung?"
> **Domain expert:** "Nein, er enthaelt getrennte Evaluationen aus demselben Schuljahr."
> **Dev:** "Hat der Lehrkraft-Export eine eigene Uebersichtsseite?"
> **Domain expert:** "Nein, das ist im ersten Scope bewusst nicht enthalten."
> **Dev:** "Wie buendelt der Lehrkraft-Export mehrere Evaluationen?"
> **Domain expert:** "Er enthaelt ein Blatt pro Evaluation im Einzel-Export-Format."
> **Dev:** "Wie heissen die Tabellenblaetter?"
> **Domain expert:** "Nach Klasse oder Lerngruppe und Fach, bei Kollisionen nummeriert."
> **Dev:** "Braucht der Export Diagramme?"
> **Domain expert:** "Nein, im ersten Scope reicht eine einfache Excel-Datei ohne Diagramme."
> **Dev:** "Analysiert die Administration Ergebnisse im Evaluationssystem?"
> **Domain expert:** "Nein, das System erzeugt nur einfache Excel-Exporte zur Weitergabe."
> **Dev:** "Enthaelt der Excel-Export trotzdem Mittelwerte?"
> **Domain expert:** "Ja, der Export enthaelt die Item-Aggregate inklusive Mittelwert."
> **Dev:** "Speichert das System erzeugte Excel-Dateien dauerhaft?"
> **Domain expert:** "Nein, Exporte werden bei Bedarf aus Item-Aggregaten erzeugt."
> **Dev:** "Welche Metadaten stehen im Einzel-Export?"
> **Domain expert:** "Schuljahr, Unterrichtsgruppe, Fragebogen-Version, Teilnehmerzahlen, Abschlussdatum und Hinweis auf aggregierte Daten."
> **Dev:** "Legt die Administration jede Unterrichtsgruppe einzeln an?"
> **Domain expert:** "Nein, Unterrichtsgruppen werden ueber einen Stammdatenimport vorbereitet."
> **Dev:** "Werden gueltige Zeilen importiert, wenn andere Zeilen fehlerhaft sind?"
> **Domain expert:** "Nein, bei Importfehlern wird der gesamte Import nicht uebernommen."
> **Dev:** "Reicht der Lehrkraftname im Import?"
> **Domain expert:** "Nein, der Import braucht auch eine eindeutige Lehrkraft-Kennung."
> **Dev:** "Was ist die bevorzugte Lehrkraft-Kennung?"
> **Domain expert:** "Die schulische E-Mail-Adresse, falls vorhanden."
> **Dev:** "Erscheint die Lehrkraft-E-Mail im QR-Material?"
> **Domain expert:** "Nein, die Lehrkraft-Kennung wird nur intern verwendet."
> **Dev:** "Darf dieselbe Unterrichtsgruppe zweimal importiert werden?"
> **Domain expert:** "Nein, doppelte Unterrichtsgruppen sind Importfehler."
> **Dev:** "Kann die Administration einen fehlerhaften Import korrigieren?"
> **Domain expert:** "Ja, aber nur durch Korrekturimport vor Nutzung der betroffenen Evaluationen."
> **Dev:** "Kann die Lehrkraft nach Verbindungsverlust weiter steuern?"
> **Domain expert:** "Ja, sie oeffnet den Lehrkraft-QR erneut und gibt ihre PIN ein."
> **Dev:** "Was bekommt die Administration nach dem Import?"
> **Domain expert:** "Vorbereitete Evaluationen und QR-Material fuer die Durchfuehrung."
> **Dev:** "Funktionieren QR-Codes sofort nach dem Import?"
> **Domain expert:** "Nein, die Administration aktiviert vorbereitete Evaluationen erst nach Pruefung."
> **Dev:** "Kann eine aktivierte Evaluation wieder deaktiviert werden?"
> **Domain expert:** "Ja, aber nur vor dem ersten Beitritt oder Start."
> **Dev:** "Kann eine Evaluation mit Antworten geloescht werden?"
> **Domain expert:** "Nein, geloescht werden nur ungenutzte Evaluationen."
> **Dev:** "Muss das System mehrere Sprachen unterstuetzen?"
> **Domain expert:** "Nein, im ersten Scope ist die Systemsprache Deutsch."
> **Dev:** "Aendert die Administration Fragebogen-Items im System?"
> **Domain expert:** "Nein, die Frageboegen sind im ersten Scope fest konfiguriert."
> **Dev:** "Aendern neue Item-Texte alte Evaluationen?"
> **Domain expert:** "Nein, jede Evaluation behaelt ihre Fragebogen-Version."
> **Dev:** "Bleiben Item-Aggregate dauerhaft gespeichert?"
> **Domain expert:** "Nein, sie bleiben fuer drei Schuljahre gespeichert."
> **Dev:** "Loescht das System alte Item-Aggregate automatisch?"
> **Domain expert:** "Nein, es markiert sie fuer einen bewussten administrativen Loeschlauf."
> **Dev:** "Bleiben Tiernamen und aktuelle Antworten nach dem Schliessen erhalten?"
> **Domain expert:** "Nein, Live-Daten werden beim Schliessen geloescht oder entkoppelt."
> **Dev:** "Bleibt eine pausierte Evaluation unbegrenzt unauffaellig offen?"
> **Domain expert:** "Nein, nach 14 Tagen wird sie pruefbeduerftig."
> **Dev:** "Protokollieren wir jede Schuelerantwort?"
> **Domain expert:** "Nein, dauerhaft protokolliert werden nur administrative Aktionen."
> **Dev:** "Nutzen Schueler und Lehrkraft denselben QR-Code?"
> **Domain expert:** "Nein, es gibt einen Schueler-QR und einen Lehrkraft-QR je Evaluation."
> **Dev:** "Wie verteilt die Administration die Zugangslinks?"
> **Domain expert:** "Als druckbares QR-Material, nicht als reine Linkliste."
> **Dev:** "Ist die Klassengroesse dasselbe wie die Zahl der Antworten?"
> **Domain expert:** "Nein, der Export unterscheidet erwartete Teilnehmerzahl, Beitritte und gueltige Antworten."
> **Dev:** "Muss die Lehrkraft warten, bis alle erwarteten Schueler beigetreten sind?"
> **Domain expert:** "Nein, sie kann bewusst trotz fehlender Beitritte starten."
> **Dev:** "Kann die Lehrkraft die erwartete Teilnehmerzahl korrigieren?"
> **Domain expert:** "Nein, die erwartete Teilnehmerzahl bleibt administrativ gepflegt."
> **Dev:** "Koennen Schueler sofort antworten, sobald ein Item erscheint?"
> **Domain expert:** "Nein, zuerst kommt die Lesephase, danach gibt die Lehrkraft die Antwortphase frei."
> **Dev:** "Kann ein Schueler seine Antwort noch aendern?"
> **Domain expert:** "Ja, bis die Lehrkraft die Antwortphase beendet."
> **Dev:** "Speichern wir die Aenderungshistorie einer Antwort?"
> **Domain expert:** "Nein, es zaehlt nur der zuletzt gewaehlte Antwortwert."
> **Dev:** "Darf die Lehrkraft einzelne Antworten ohne Namen sehen?"
> **Domain expert:** "Nein, die Lehrkraft sieht nur Aggregationen."
> **Dev:** "Muessen wir einzelne Antworten speichern, um technische Ausfaelle zu erkennen?"
> **Domain expert:** "Nein, dafuer speichern wir Item-Aggregate mit fehlenden Antworten und Zaehlern je Antwortwert."
> **Dev:** "Wann wird das Ergebnis einer Frage dauerhaft fixiert?"
> **Domain expert:** "Wenn die Lehrkraft zur naechsten Frage fortfaehrt."
> **Dev:** "Muss der QR-Code nach einer Unterrichtsstunde verfallen?"
> **Domain expert:** "Nein, eine pausierte Evaluation kann in der naechsten Stunde fortgesetzt werden."
> **Dev:** "Kann ein neuer Schueler in Stunde zwei noch beitreten?"
> **Domain expert:** "Nein, nach dem Start des ersten Items gibt es nur noch Wiederbeitritt."
> **Dev:** "Reicht der Lehrkraft-QR allein zum Steuern der Evaluation?"
> **Domain expert:** "Nein, die Lehrkraft braucht zusaetzlich ihre vierstellige PIN."
> **Dev:** "Kann die Lehrkraft mit der PIN spaeter Ergebnisse ansehen?"
> **Domain expert:** "Nein, die PIN gilt nur fuer die Durchfuehrung."
> **Dev:** "Importiert die Administration Lehrkraft-PINs?"
> **Domain expert:** "Nein, das System erzeugt Lehrkraft-PINs automatisch."
> **Dev:** "Wird eine Evaluation nach falschen PINs gesperrt?"
> **Domain expert:** "Nein, PIN-Fehlversuche koennen verzoegert werden, aber blockieren nicht die Evaluation."
> **Dev:** "Kann eine bekannt gewordene PIN ersetzt werden?"
> **Domain expert:** "Ja, die Administration kann eine PIN-Rotation ausloesen."

## Flagged ambiguities

- "Kurs" wurde als Kombination aus Schuljahr, Klasse oder Lerngruppe, Fach und Lehrkraft verwendet; aufgeloest als **Unterrichtsgruppe**.
- "Schueler" bezeichnet im Auswertungskontext keine gespeicherte reale Person; aufgeloest als anonyme **Teilnahme**.
- "Antworten" werden nicht als zusammenhaengender Antwortbogen verstanden; aufgeloest als einzelne **Item-Antworten** ohne dauerhaftes Profil.
- "Direktor", "Admin" und "Verwaltung" wurden fuer die vorbereitende und voll zugriffsberechtigte Rolle verwendet; aufgeloest als **Administration**.
- "Oberstufe" bezeichnet hier die schulinterne Fragebogen-Gruppe fuer Klassenstufen 7 bis 10, nicht zwingend die gymnasiale Oberstufe.
- "Keine Angabe" ist keine Antwortoption im ersten Scope; technisch nicht abgegebene Werte werden als **Fehlende Antwort** verstanden.
- "Abgeschlossen" bedeutet nicht automatisch "fuer die Lehrkraft sichtbar"; Sichtbarkeit entsteht erst durch **Freigegebene Ergebnisse**.
- "Rohdaten" sind fuer Lehrkraefte nicht sichtbar; Lehrkraefte sehen nur **Aggregationen**.
- "Rohdaten speichern" wurde datensparsamer als dauerhaft gespeicherte **Item-Aggregate** aufgeloest, nicht als Speicherung einzelner Antwortereignisse.
- "Abgebrochen" bedeutet nicht automatisch geschlossen; eine nicht beendete Evaluation kann als **Pausierte Evaluation** fortgesetzt oder durch die **Administration** geschlossen werden.
- "Auswertung" bezeichnet im ersten Scope keine interaktive Analyseoberflaeche; aufgeloest als **Exportfunktion**.
