# JUDO Cloud für Home Assistant

Version 0.3.3

Inoffizielle Custom Integration für ältere JUDO-Connectivity-Module (z. B. eWAC
FW 1.13), die über das myJUDO-Portal erreichbar sind, aber keine lokale
`/api/rest/`-Schnittstelle bereitstellen.

## Installation

1. Den Ordner `custom_components/judo_cloud` aus diesem Paket nach
   `/config/custom_components/judo_cloud` in Home Assistant kopieren.
2. Home Assistant vollständig neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → JUDO Cloud**.
4. Benutzername und Passwort der JU-Control-App eingeben.

Bei mehreren Anlagen erscheint anschließend eine Geräteauswahl. Das
Abfrageintervall beträgt fünf Minuten, um die Hersteller-Cloud nicht unnötig
zu belasten.

## Entitäten

- enthärtete Weichwassermenge (Gesamtzähler)
- Gerätestatus/Verbindung
- Schaltfläche **Regeneration starten**
- Schaltfläche **Salz auffüllen (25 kg)**
- geschätzter Salzverbrauch seit der letzten Befüllung
- geschätzter Salzvorrat und Füllstand
- geschätzte Salzreichweite
- geschätzte Anzahl verbleibender Regenerationen

Die bisherigen Cloud-Werte für Gesamtwasser, Durchfluss, Resthärte,
Salzregister und Standby wurden entfernt, da sie bei der SOFTwell S mit älterem
eWAC dauerhaft `0` liefern.

## Salzschätzung einrichten

1. Nach dem Befüllen in der Geräteansicht die Entität
   **Salzmenge nach Befüllung** auf die tatsächlich eingefüllte Menge setzen.
2. Mit dem Speichern werden die aktuelle Weichwassermenge und der Zeitpunkt als
   Ausgangspunkt hinterlegt.
3. Ab dann werden die Salzsensoren aus dem Zuwachs der enthärteten Wassermenge
   berechnet.

Bei einer späteren Befüllung kann einfach die Schaltfläche **Salz auffüllen
(25 kg)** gedrückt werden. Sie addiert 25 kg zum aktuell geschätzten Restvorrat,
begrenzt das Ergebnis auf die Behälterkapazität von 50 kg und setzt den
Berechnungsstand auf die aktuelle Weichwassermenge. Ist noch kein Ausgangswert
vorhanden, beginnt die Berechnung mit 25 kg.

Als Standard werden `0,4 kg` Salz je Kubikmeter Weichwasser verwendet. Dieser
Wert entspricht dem JUDO-Richtwert für eine Enthärtung von 20 °dH auf 8 °dH.
Die standardmäßig deaktivierte Entität **Salzverbrauch je m³ Weichwasser** kann
bei Bedarf aktiviert und an die eigene Wasserhärte beziehungsweise den realen
Verbrauch angepasst werden.

Die SOFTwell S misst beim älteren eWAC keinen verlässlich abrufbaren,
kontinuierlichen Salzfüllstand. Deshalb sind alle Salzwerte ausdrücklich als
Schätzung gekennzeichnet. Bis die Salzmenge einmal gesetzt wurde, bleiben diese
Sensoren nicht verfügbar und zeigen keine irreführende Null an.

## Hinweise

- Der Abruf wurde erfolgreich an einer SOFTwell S mit eWAC FW 1.13 getestet.
- Der Befehl zum Starten einer Regeneration verwendet den vom ioBroker-Adapter
  bekannten Cloud-Registerbefehl 65. Er sollte erst bei Bedarf gedrückt werden.
- Die Zugangsdaten bleiben im Home-Assistant-Konfigurationseintrag. Das Passwort
  wird für die Anmeldung entsprechend dem Verhalten des ioBroker-Adapters als
  MD5-Hash an myJUDO übertragen.
- Die Cloud-Schnittstelle ist nicht öffentlich dokumentiert und kann sich ändern.
- Unter **Einstellungen → Geräte & Dienste → JUDO Cloud → Diagnose
  herunterladen** kann ein bereinigter Registerauszug erzeugt werden. Er enthält
  keine Zugangsdaten und hilft dabei, künftig weitere echte Gerätewerte
  eindeutig zuzuordnen.


Die Protokoll- und Registerdekodierung basiert auf dem MIT-lizenzierten Projekt
`ioBroker.judoisoft` von Arthur Rupp. Dessen Lizenztext liegt diesem Paket bei.

## Branding

Das Paket enthält ein lokales JUDO-Symbol und -Logo in normaler sowie
hochauflösender Ausführung. Home Assistant verwendet lokale Branding-Dateien
bei Custom Integrations ab Version 2026.3 automatisch.
