#!/usr/bin/env python3
"""Haalt de komende afspraken uit de Google Calendar-feed en schrijft index.html.

De pagina krijgt een ruime voorraad afspraken mee (standaard 120 dagen) en kiest
in de browser zelf welke er getoond worden. Daardoor klopt het scherm ook als
de nachtelijke build een paar dagen niet gedraaid heeft, en schuift het om
middernacht vanzelf door zonder herladen.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from zoneinfo import ZoneInfo

import requests
import icalendar
import recurring_ical_events

ICS_URL = ("https://calendar.google.com/calendar/ical/"
           "mellegbs%40gmail.com/public/basic.ics")

SCHOOL_NAAM = "Basisschool Het Park"
WEBSITE = "www.basisschoolhetpark.be"

# Hoeveel dagen vooruit we afspraken meegeven aan de pagina.
VENSTER_DAGEN = 120
# Titels die Google invult voor privé-afspraken; die horen niet op een scherm.
NEGEER = {"busy", "bezet", "(no title)", "zonder titel"}

TZ = ZoneInfo("Europe/Brussels")
TIMEOUT = 30

MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]


def naar_lokaal(waarde):
    """Google levert tijdstippen in UTC. Zonder omrekenen naar Europe/Brussels
    valt een avondafspraak een dag te vroeg."""
    if isinstance(waarde, dt.datetime):
        if waarde.tzinfo is None:
            waarde = waarde.replace(tzinfo=TZ)
        return waarde.astimezone(TZ)
    return waarde


def haal_afspraken(ics_tekst: str, vanaf: dt.date, tot: dt.date) -> list[dict]:
    kalender = icalendar.Calendar.from_ical(ics_tekst)

    # of() klapt terugkerende afspraken uit. Zonder deze stap toont een
    # wekelijkse zwemles alleen zijn allereerste datum, en verdwijnt hij dus
    # volledig van het scherm.
    events = recurring_ical_events.of(kalender).between(vanaf, tot)

    afspraken = []
    for ev in events:
        titel = str(ev.get("SUMMARY", "")).strip()
        if not titel or titel.lower() in NEGEER:
            continue

        rauw_start = ev["DTSTART"].dt
        heledag = not isinstance(rauw_start, dt.datetime)
        start = naar_lokaal(rauw_start)

        if "DTEND" in ev:
            eind = naar_lokaal(ev["DTEND"].dt)
            if heledag:
                # Bij hele-dag-afspraken is DTEND exclusief.
                eind -= dt.timedelta(days=1)
                if eind < start:
                    eind = start
        else:
            eind = start

        afspraken.append({
            "titel": titel,
            "heledag": heledag,
            "start": start.isoformat(),
            "eind": eind.isoformat(),
            "tijd": None if heledag else f"{start.hour:02d}:{start.minute:02d}",
            "locatie": str(ev.get("LOCATION", "")).strip()[:80],
        })

    afspraken.sort(key=lambda a: (a["start"], a["titel"]))
    return afspraken


def bouw_html(afspraken: list[dict], vandaag: dt.date) -> str:
    payload = json.dumps(
        {"bijgewerkt_op": vandaag.isoformat(), "afspraken": afspraken},
        ensure_ascii=False,
    ).replace("<", "\\u003c")   # zodat een titel het script niet kan afsluiten

    bijgewerkt = f"{vandaag.day} {MAANDEN[vandaag.month - 1]} {vandaag.year}"

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1920, initial-scale=1">
<title>Kalender {SCHOOL_NAAM}</title>
<link rel="preconnect" href="https://api.fontshare.com" crossorigin>
<link rel="stylesheet"
      href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600,700&display=swap">
<link rel="stylesheet" href="styles.css">
</head>
<body>

<div id="scherm">
  <header>
    <div>
      <div class="merk">{SCHOOL_NAAM}</div>
      <div class="titel">Wat staat er op de kalender</div>
    </div>
    <div class="vandaag" id="vandaag"></div>
  </header>

  <main id="inhoud">
    <noscript><p class="leeg">Zet JavaScript aan om de kalender te tonen.</p></noscript>
  </main>

  <footer>
    <span>Volledige kalender op {WEBSITE}</span>
    <span class="dim">Bijgewerkt op {bijgewerkt}</span>
  </footer>
</div>

<script>
const DATA = {payload};

// Hoeveel afspraken er op het scherm passen.
const MAX_AFSPRAKEN = 7;
// Elke 30 minuten de pagina opnieuw ophalen, zodat een nieuwe build binnenkomt.
const HERLAAD_MS = 30 * 60 * 1000;

const WEEKDAGEN = ["zondag", "maandag", "dinsdag", "woensdag", "donderdag",
                   "vrijdag", "zaterdag"];
const MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
                 "augustus", "september", "oktober", "november", "december"];

function dagVan(d) {{ return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }}
function esc(s) {{
  return String(s).replace(/[&<>"]/g, c =>
    ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }}[c]));
}}
function dagLabel(dag, vandaag) {{
  const verschil = Math.round((dag - vandaag) / 86400000);
  const datum = WEEKDAGEN[dag.getDay()] + " " + dag.getDate() + " " +
                MAANDEN[dag.getMonth()];
  if (verschil === 0) return {{ klem: "Vandaag", datum: datum }};
  if (verschil === 1) return {{ klem: "Morgen", datum: datum }};
  return {{ klem: null, datum: datum }};
}}

function teken() {{
  const nu = new Date();
  const vandaag = dagVan(nu);
  document.getElementById("vandaag").textContent =
    WEEKDAGEN[nu.getDay()] + " " + nu.getDate() + " " + MAANDEN[nu.getMonth()];

  // Een afspraak blijft staan tot ze voorbij is, niet tot ze begonnen is.
  const komend = DATA.afspraken.filter(a => {{
    const eind = new Date(a.eind);
    return a.heledag ? dagVan(eind) >= vandaag : eind >= nu;
  }}).slice(0, MAX_AFSPRAKEN);

  const inhoud = document.getElementById("inhoud");
  if (komend.length === 0) {{
    inhoud.innerHTML = '<p class="leeg">Geen afspraken gepland.</p>';
    return;
  }}

  // Per dag groeperen zodat dezelfde datum niet vier keer onder elkaar staat.
  const dagen = [];
  komend.forEach(a => {{
    const sleutel = a.start.slice(0, 10);
    let groep = dagen.find(d => d.sleutel === sleutel);
    if (!groep) {{
      groep = {{ sleutel: sleutel, dag: dagVan(new Date(a.start)), items: [] }};
      dagen.push(groep);
    }}
    groep.items.push(a);
  }});

  let html = '';
  dagen.forEach(groep => {{
    const label = dagLabel(groep.dag, vandaag);
    html += '<section class="dag' + (label.klem ? ' nabij' : '') + '">' +
      '<h2>' + (label.klem ? '<span class="klem">' + label.klem + '</span>' : '') +
        '<span class="dagdatum">' + esc(label.datum) + '</span></h2><ul>';
    groep.items.forEach(a => {{
      html += '<li>' +
        '<span class="tijd">' + (a.heledag ? 'hele dag' : esc(a.tijd)) + '</span>' +
        '<span class="titel">' + esc(a.titel) +
          (a.locatie ? '<span class="plek"> \\u00b7 ' + esc(a.locatie) + '</span>' : '') +
        '</span></li>';
    }});
    html += '</ul></section>';
  }});
  inhoud.innerHTML = html;
}}

// Een scherm dat maandenlang hetzelfde toont brandt in. Elke vijf minuten
// een paar pixels opschuiven is genoeg om dat te voorkomen.
const SCHUIF = [[0,0],[2,1],[3,0],[2,-1],[0,-2],[-2,-1],[-3,0],[-2,1]];
let schuifIndex = 0;
function pixelShift() {{
  const [x, y] = SCHUIF[schuifIndex % SCHUIF.length];
  document.getElementById("scherm").style.transform =
    "translate(" + x + "px," + y + "px)";
  schuifIndex++;
}}

teken();
pixelShift();
setInterval(teken, 60 * 1000);
setInterval(pixelShift, 5 * 60 * 1000);
setTimeout(() => location.reload(), HERLAAD_MS);
</script>

</body>
</html>
"""


def main() -> int:
    vandaag = dt.datetime.now(TZ).date()
    tot = vandaag + dt.timedelta(days=VENSTER_DAGEN)

    print(f"Kalender ophalen ({vandaag} t.e.m. {tot}) ...")
    resp = requests.get(ICS_URL, timeout=TIMEOUT,
                        headers={"User-Agent": "ical2html/2.0"})
    resp.raise_for_status()

    afspraken = haal_afspraken(resp.text, vandaag, tot)
    print(f"{len(afspraken)} afspraak/afspraken gevonden")
    for a in afspraken[:10]:
        print(f"  {a['start'][:16].replace('T', ' ')}  "
              f"{'hele dag' if a['heledag'] else a['tijd']:<9} {a['titel'][:50]}")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(bouw_html(afspraken, vandaag))
    print("index.html geschreven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
