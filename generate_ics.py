import json
import urllib.request
import urllib.error
import ssl
import sys
from datetime import datetime, timezone

# --- KOORDINATEN (Neukirchen OT Adorf) ---
LATITUDE = 50.7725
LONGITUDE = 12.8860

# Katalog für ~50.8° N mit Deklination (dec) zur Zenit-Berechnung
DSO_CATALOG = [
    {"cat": "M109", "name": "Spiralgalaxie Ursa Major", "dec": 53.4, "months": [2, 3, 4, 5, 6]},
    {"cat": "M51", "name": "Whirlpool-Galaxie", "dec": 47.2, "months": [2, 3, 4, 5, 6, 7]},
    {"cat": "M106", "name": "Spiralgalaxie Canes Venatici", "dec": 47.3, "months": [2, 3, 4, 5, 6]},
    {"cat": "M101", "name": "Feuerrad-Galaxie", "dec": 54.4, "months": [3, 4, 5, 6, 7]},
    {"cat": "M97", "name": "Eulennebel", "dec": 55.0, "months": [2, 3, 4, 5, 6]},
    {"cat": "M63", "name": "Sonnenblumen-Galaxie", "dec": 42.0, "months": [3, 4, 5, 6, 7]},
    {"cat": "M3", "name": "Kugelsternhaufen Jagdhunde", "dec": 28.4, "months": [3, 4, 5, 6, 7]},
    {"cat": "M104", "name": "Sombrero-Galaxie", "dec": -11.6, "months": [3, 4, 5, 6]},
    {"cat": "M13", "name": "Herkules-Kugelsternhaufen", "dec": 36.5, "months": [4, 5, 6, 7, 8, 9]},
    {"cat": "M92", "name": "Kugelsternhaufen Herkules", "dec": 43.1, "months": [5, 6, 7, 8, 9]},
    {"cat": "M57", "name": "Ringnebel", "dec": 33.0, "months": [5, 6, 7, 8, 9, 10]},
    {"cat": "M27", "name": "Hantelnebel", "dec": 22.7, "months": [5, 6, 7, 8, 9, 10]},
    {"cat": "NGC 7000", "name": "Nordamerika-Nebel", "dec": 44.4, "months": [5, 6, 7, 8, 9, 10]},
    {"cat": "NGC 6992 / 6960", "name": "Schleiernebel (Veil)", "dec": 31.7, "months": [6, 7, 8, 9, 10, 11]},
    {"cat": "NGC 6888", "name": "Crescent-Nebel", "dec": 38.4, "months": [6, 7, 8, 9, 10]},
    {"cat": "IC 1396", "name": "Elefantenrüsselnebel", "dec": 57.5, "months": [7, 8, 9, 10, 11]},
    {"cat": "IC 5146", "name": "Kokon-Nebel", "dec": 47.3, "months": [7, 8, 9, 10, 11]},
    {"cat": "M31", "name": "Andromeda-Galaxie", "dec": 41.2, "months": [8, 9, 10, 11, 12, 1]},
    {"cat": "IC 1805", "name": "Herznebel", "dec": 61.5, "months": [8, 9, 10, 11, 12, 1]},
    {"cat": "IC 1848", "name": "Seelennebel", "dec": 60.4, "months": [8, 9, 10, 11, 12, 1]},
    {"cat": "NGC 869 / 884", "name": "Doppelsternhaufen h & chi", "dec": 57.1, "months": [8, 9, 10, 11, 12, 1, 2]},
    {"cat": "NGC 281", "name": "Pacman-Nebel", "dec": 56.6, "months": [8, 9, 10, 11, 12]},
    {"cat": "NGC 7331", "name": "Deer Lick Gruppe", "dec": 34.4, "months": [8, 9, 10, 11, 12]},
    {"cat": "M33", "name": "Dreiecks-Galaxie", "dec": 30.6, "months": [9, 10, 11, 12, 1]},
    {"cat": "NGC 1499", "name": "Kaliforniennebel", "dec": 36.6, "months": [9, 10, 11, 12, 1, 2]},
    {"cat": "NGC 891", "name": "Outer Line Galaxie", "dec": 42.4, "months": [9, 10, 11, 12, 1]},
    {"cat": "NGC 1333", "name": "Reflexionsnebel Perseus", "dec": 31.4, "months": [9, 10, 11, 12, 1]},
    {"cat": "M74", "name": "Phantom-Galaxie", "dec": 15.8, "months": [9, 10, 11, 12, 1]},
    {"cat": "M45", "name": "Plejaden", "dec": 24.1, "months": [10, 11, 12, 1, 2]},
    {"cat": "M42 / M43", "name": "Orionnebel", "dec": -5.4, "months": [11, 12, 1, 2, 3]},
    {"cat": "IC 434 / B33", "name": "Pferdekopfnebel", "dec": -2.5, "months": [11, 12, 1, 2, 3]},
    {"cat": "M1", "name": "Krebsnebel", "dec": 22.0, "months": [11, 12, 1, 2, 3, 4]},
    {"cat": "IC 405", "name": "Flammensternnebel", "dec": 34.4, "months": [11, 12, 1, 2, 3]},
    {"cat": "NGC 2403", "name": "Spiralgalaxie Camelopardalis", "dec": 65.6, "months": [11, 12, 1, 2, 3, 4]},
    {"cat": "NGC 2237", "name": "Rosettennebel", "dec": 5.0, "months": [12, 1, 2, 3, 4]},
    {"cat": "M78", "name": "Reflexionsnebel Orion", "dec": 0.1, "months": [12, 1, 2, 3]},
    {"cat": "M81 / M82", "name": "Bodes Galaxie & Zigarre", "dec": 69.1, "months": [12, 1, 2, 3, 4, 5]},
    {"cat": "M16", "name": "Adlernebel (Säulen)", "dec": -13.8, "months": [5, 6, 7, 8]},
    {"cat": "M17", "name": "Omega- / Schwanennebel", "dec": -16.2, "months": [5, 6, 7, 8]},
    {"cat": "M8", "name": "Lagunennebel", "dec": -24.4, "months": [6, 7, 8]},
    {"cat": "M20", "name": "Trifidnebel", "dec": -23.0, "months": [6, 7, 8]}
]

def get_sorted_targets(month):
    matched = []
    for t in DSO_CATALOG:
        if month in t['months']:
            max_alt = round(90.0 - abs(LATITUDE - t['dec']))
            matched.append({"cat": t['cat'], "name": t['name'], "max_alt": max_alt})
    matched.sort(key=lambda x: x['max_alt'], reverse=True)
    formatted = [f"• {t['cat']} ({t['name']}) - Max. Höhe: {t['max_alt']}°" for t in matched]
    return formatted if formatted else ["• Keine Objekte gelistet"]

def format_time_str(iso_str):
    if not iso_str or iso_str == "N/A" or len(iso_str) < 16:
        return "N/A"
    return iso_str[-5:]

def iso_to_ics_dt(iso_str):
    if not iso_str or len(iso_str) < 16:
        return None
    clean = iso_str.replace("-", "").replace(":", "")
    return clean[:15] + "00"

def generate_ics():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,"
        f"relative_humidity_2m,precipitation_probability,precipitation,is_day&"
        f"daily=sunrise,sunset,moonrise,moonset,moon_phase&"
        f"forecast_days=7&timezone=auto"
    )
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("Lade Wetter- & Astrodaten von Open-Meteo...")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"API Fehler-Details: {error_body}", file=sys.stderr)
        raise e

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    
    clouds_hourly = hourly.get("cloud_cover", [])
    clouds_low = hourly.get("cloud_cover_low", [])
    clouds_mid = hourly.get("cloud_cover_mid", [])
    clouds_high = hourly.get("cloud_cover_high", [])
    humidity_hourly = hourly.get("relative_humidity_2m", [])
    precip_prob_hourly = hourly.get("precipitation_probability", [])
    precip_hourly = hourly.get("precipitation", [])
    is_day_hourly = hourly.get("is_day", [])
    times_hourly = hourly.get("time", [])
    
    sunsets = daily.get("sunset", [])
    sunrises = daily.get("sunrise", [])
    moonrises = daily.get("moonrise", [])
    moonsets = daily.get("moonset", [])
    moon_phases = daily.get("moon_phase", [])

    events = []

    for day in range(7):
        start_idx = day * 24
        end_idx = start_idx + 24
        
        night_indices = [k for k in range(start_idx, end_idx) if is_day_hourly[k] == 0]
        if not night_indices:
            night_indices = list(range(start_idx, end_idx))
            
        n_clouds = [clouds_hourly[k] for k in night_indices]
        n_low = [clouds_low[k] for k in night_indices] if clouds_low else n_clouds
        n_mid = [clouds_mid[k] for k in night_indices] if clouds_mid else n_clouds
        n_high = [clouds_high[k] for k in night_indices] if clouds_high else n_clouds
        
        n_humidity = [humidity_hourly[k] for k in night_indices]
        n_precip_prob = [precip_prob_hourly[k] for k in night_indices]
        n_precip = [precip_hourly[k] for k in night_indices]
        
        avg_cloud = sum(n_clouds) / len(n_clouds) if n_clouds else 50
        avg_low = sum(n_low) / len(n_low) if n_low else avg_cloud
        avg_mid = sum(n_mid) / len(n_mid) if n_mid else avg_cloud
        avg_high = sum(n_high) / len(n_high) if n_high else avg_cloud
        
        avg_humidity = sum(n_humidity) / len(n_humidity) if n_humidity else 50
        max_precip_prob = max(n_precip_prob) if n_precip_prob else 0
        total_precip = sum(n_precip) if n_precip else 0.0
        
        # Monddaten
        moon_phase_val = moon_phases[day] if day < len(moon_phases) else 0.5
        moon_illumination = int((1 - abs(moon_phase_val - 0.5) * 2) * 100)
        m_rise = format_time_str(moonrises[day] if day < len(moonrises) else "")
        m_set = format_time_str(moonsets[day] if day < len(moonsets) else "")
        
        # Sonnenuntergang & -aufgang
        sunset_raw = sunsets[day] if day < len(sunsets) else ""
        sunrise_raw = sunrises[day+1] if (day+1) < len(sunrises) else (sunrises[day] if day < len(sunrises) else "")
        
        sunset_time = format_time_str(sunset_raw)
        sunrise_time = format_time_str(sunrise_raw)
        
        # Score-Berechnung: Tiefe/Mittlere Wolken wiegen schwerer als hohe Schleierwolken
        weighted_cloud = (avg_low * 0.5) + (avg_mid * 0.3) + (avg_high * 0.2)
        cloud_score = (100 - weighted_cloud) * 0.70
        moon_score = (100 - moon_illumination) * 0.20
        humidity_score = (100 - max(0, avg_humidity - 70) * 3.33) * 0.10
        precip_penalty = (max_precip_prob / 100.0) * 30
        
        total_score = max(0, min(100, int(cloud_score + moon_score + humidity_score - precip_penalty)))
        
        # Nur Gelb (>=45%) und Grün (>=70%) anzeigen
        if total_score < 45:
            continue
            
        date_str = times_hourly[start_idx][:10]
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        status_icon = "🟢" if total_score >= 70 else "🟡"
        summary = f"🔭 {status_icon} Deep Sky: {total_score}%"
        
        targets = get_sorted_targets(dt_obj.month)
        targets_str = "\\n".join(targets)
        
        dew_warning = " ⚠️ (Tau-Risiko)" if avg_humidity >= 85 else ""
        precip_str = f"{max_precip_prob}% ({total_precip:.1f} mm)" if max_precip_prob > 0 else "0% (Trocken)"
        
        description = (
            f"Nachtfenster (Sonnenunter/aufgang): {sunset_time} - {sunrise_time} Uhr\\n"
            f"Bewölkung (Nacht): Tiefe {int(avg_low)}% | Mid {int(avg_mid)}% | High {int(avg_high)}% (Schnitt: {int(avg_cloud)}%)\\n"
            f"Mond: ~{moon_illumination}% | Aufgang: {m_rise} | Untergang: {m_set}\\n"
            f"Niederschlag: {precip_str}\\n"
            f"Luftfeuchtigkeit: {int(avg_humidity)}%{dew_warning}\\n\\n"
            f"Sichtbare Objekte (sortiert nach Zenithöhe):\\n"
            f"{targets_str}\\n\\n"
            f"Erstellt via Open-Meteo Astro API"
        )
        
        dt_start_ics = iso_to_ics_dt(sunset_raw)
        dt_end_ics = iso_to_ics_dt(sunrise_raw)
        
        if dt_start_ics and dt_end_ics:
            dt_lines = f"DTSTART:{dt_start_ics}\nDTEND:{dt_end_ics}"
        else:
            dt_start = date_str.replace("-", "")
            dt_lines = f"DTSTART;VALUE=DATE:{dt_start}"
            
        # VALARM: Sendet genau 6 Stunden vor Beginn des Ereignisses eine Benachrichtigung
        alarm_block = """BEGIN:VALARM
TRIGGER:-PT6H
ACTION:DISPLAY
DESCRIPTION:🔭 Deep Sky Fotografie: Gute Bedingungen heute Nacht!
END:VALARM"""

        events.append(f"""BEGIN:VEVENT
UID:astro-{date_str}@deepsky
DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}
{dt_lines}
SUMMARY:{summary}
DESCRIPTION:{description}
{alarm_block}
END:VEVENT""")

    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//DeepSkyForecast//DE\nX-WR-CALNAME:Deep Sky Vorhersage\n" + "\n".join(events) + "\nEND:VCALENDAR"
    
    with open("deepsky.ics", "w", encoding="utf-8") as f:
        f.write(ics_content)
    print("Vollständig optimierte deepsky.ics erfolgreich erstellt!")

if __name__ == "__main__":
    generate_ics()
