# 🌊 ValueFlow – Strategic Prioritization Board

[![No Backend](https://img.shields.io/badge/Architecture-No%20Backend-success)](#)
[![Vanilla JS](https://img.shields.io/badge/Tech-Vanilla%20JS%20%7C%20HTML5-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Das strategische Filter-Board *vor* deinem Jira. Stoppt Feature-Creep, visualisiert Impact vs. Effort und erzwingt kompromissloses Alignment zwischen Business & Tech.**

[🚀 **ZUR LIVE DEMO**](https://DEIN-GITHUB-NAME.github.io/ValueFlow) *(Link später anpassen)*

---

## 🛑 Das Problem
Roadmap-Meetings enden oft in endlosen Diskussionen. Das Business fordert alles ("strategisch kritisch"), Engineering winkt ab ("zu hoher Aufwand"). Am Ende gewinnt das Bauchgefühl, der HiPPO (Highest Paid Person's Opinion) oder derjenige, der am lautesten spricht.

## 💡 Die Lösung
**ValueFlow** ist ein leichtgewichtiges, browserbasiertes Kanban-Board mit integrierter **Value vs. Effort Matrix** und harten Governance-Regeln. Es zwingt cross-funktionale Teams in die Diskussion und macht Entscheidungen transparent.

### ✨ Core Features
*   📊 **Auto-generierte 2x2 Matrix:** Trage Scores (1-5) für *Business Value* und *Tech Effort* ein. ValueFlow plottet die Initiativen live in Quadranten (Quick Wins, Major Projects, Fill-ins, Time Sinks).
*   🛡️ **Eingebaute Governance (Business Rules):** 
    *   *Sperre:* Abgelehnte Karten werden eingefroren (`Locked`) und können nicht mehr geschoben werden.
    *   *Gatekeeper:* Nur explizit "Freigegebene" Initiativen dürfen in die Spalte "Ready for Dev" wandern.
*   💾 **Workspace Sync (.json):** Keine Datenbank nötig. Lade das Board rüber als verschlüsselte Datei herunter und teile sie via Slack/Teams mit Kollegen, um asynchron weiterzuarbeiten.
*   🕓 **Audit Trail:** Jede Statusänderung wird mit Timestamp als Historie direkt an der Karte gespeichert.
*   🌓 **Dark Mode:** Out of the box, speichert die User-Präferenz im LocalStorage.

---

## 🛠️ Installation & Setup
Es gibt kein Setup! Die gesamte Web-App läuft offline in einer einzigen HTML-Datei. Kein npm, kein webpack, keine Datenbank-Verbindung nötig.

1. Lade die `index.html` herunter.
2. Mache einen Doppelklick darauf (öffnet sich im Browser).
3. Fertig.

> **Datenschutz:** Alle Daten werden im `localStorage` deines Browsers gespeichert. Es fließen keine Daten an externe Server.

---

## 🎯 Wie nutzt man es im Team? (Der PM-Workflow)
1. **Backlog Refinement:** Sammle alle groben Ideen in der ersten Spalte.
2. **Alignment-Meeting:** Screen-Sharing an. Besprecht die Karten kurz.
3. **Scoring:** Business vergibt den Value (1-5), Tech schätzt den Aufwand (1-5).
4. **Die Matrix:** Öffne die Matrix 📈. Zieht zusammen die Konsequenzen:
   * *Oben Links (Quick Wins):* Gehen sofort auf Status "Freigegeben".
   * *Unten Rechts (Time Sinks):* Gehen sofort auf "Abgelehnt".
5. **Session speichern:** Board als Workspace herunterladen und als "Decision Log" an das Team schicken.

---

## 🤝 Contributing
Fühl dich frei, das Projekt zu forken und Pull Requests für ein besseres Styling oder neue Features zu öffnen!

## 📜 License
Unter der [MIT License](LICENSE) veröffentlicht.