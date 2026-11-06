# Heatpump Efficiency (Wärmepumpe Effizienz – COP / AZ / JAZ)

Eine benutzerdefinierte Home Assistant Integration zur automatischen Berechnung der Effizienz (Arbeitszahl / JAZ / COP) einer Wärmepumpe für **Heute**, **Monat**, **Jahr** und **Gesamt** – jeweils unterteilt in **Heizung**, **Warmwasser** und **Gesamteffizienz**.

## Features

- **Einfache Einrichtung über die UI (Config Flow & Options Flow)**:
  Wähle einfach die 4 Gesamtzähler-Sensoren (`total_increasing`, z. B. in `kWh` oder `Wh`) deiner Wärmepumpe aus:
  1. Verbrauchte elektrische Energie – Heizung
  2. Erzeugte Wärmeenergie – Heizung
  3. Verbrauchte elektrische Energie – Warmwasser
  4. Erzeugte Wärmeenergie – Warmwasser
- **Automatische Zeitraum-Berechnung**:
  Berechnet automatisch die Deltas für **Heute**, **Monat** und **Jahr** (mit automatischem Reset um Mitternacht bzw. zum Monats-/Jahreswechsel) sowie den **Gesamt**-Wert über die gesamte Laufzeit.
- **Neustart-sicher (RestoreEntity)**:
  Alle Zwischenstände der Zeiträume (Heute, Monat, Jahr) bleiben bei einem Neustart von Home Assistant erhalten.
- **Automatische Einheiten-Konvertierung**:
  Unterstützt Sensoren in `Wh`, `kWh`, `MWh` und `GWh` und rechnet diese intern auf `kWh` um.
- **12 übersichtliche Sensoren unter einem Gerät**:

| Zeitraum | Heizung | Warmwasser | Gesamteffizienz |
| :--- | :--- | :--- | :--- |
| **Heute** | Effizienz Heizung Heute | Effizienz Warmwasser Heute | Gesamteffizienz Heute |
| **Monat** | Effizienz Heizung Monat | Effizienz Warmwasser Monat | Gesamteffizienz Monat |
| **Jahr** | Effizienz Heizung Jahr | Effizienz Warmwasser Jahr | Gesamteffizienz Jahr |
| **Gesamt** | Effizienz Heizung Gesamt | Effizienz Warmwasser Gesamt | Gesamteffizienz Gesamt |

## Berechnungsformeln

- **Effizienz Heizung** = $\frac{\text{Erzeugte Wärmeenergie Heizung (kWh)}}{\text{Verbrauchte elektrische Energie Heizung (kWh)}}$
- **Effizienz Warmwasser** = $\frac{\text{Erzeugte Wärmeenergie Warmwasser (kWh)}}{\text{Verbrauchte elektrische Energie Warmwasser (kWh)}}$
- **Gesamteffizienz** = $\frac{\text{Erzeugte Wärme Heizung} + \text{Erzeugte Wärme Warmwasser}}{\text{Verbrauchte Energie Heizung} + \text{Verbrauchte Energie Warmwasser}}$

Zusätzlich stellt jeder Sensor in seinen Attributen (`extra_state_attributes`) die im jeweiligen Zeitraum verbrauchte (`consumed_kwh`) und erzeugte (`produced_kwh`) Energiemenge bereit.

## Installation

### Über HACS (Custom Repository)

1. Öffne **HACS** in Home Assistant.
2. Klicke oben rechts auf das Drei-Punkte-Menü und wähle **Benutzerdefinierte Repositories** (*Custom repositories*).
3. Füge die URL dieses Repositories hinzu und wähle als Kategorie **Integration** (bzw. *Integration*).
4. Installiere **Heatpump Efficiency (COP / JAZ / AZ)** und starte Home Assistant neu.

### Manuelle Installation

1. Kopiere den Ordner `custom_components/heatpump_efficiency` in das Verzeichnis `<config>/custom_components/` deiner Home Assistant Installation.
2. Starte Home Assistant neu.

## Konfiguration

1. Gehe in Home Assistant zu **Einstellungen** -> **Geräte & Dienste**.
2. Klicke unten rechts auf **Integration hinzufügen** und suche nach **Heatpump Efficiency**.
3. Vergib einen Namen (Standard: `Wärmepumpe Effizienz`) und wähle die 4 Energiesensoren aus.
4. Über **Konfigurieren** bei der eingerichteten Integration können die Sensoren jederzeit nachträglich angepasst werden.
