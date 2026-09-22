import json
import urllib.request
import urllib.error
import ssl
import sys
import math
from datetime import datetime, timezone, timedelta

# --- KOORDINATEN (Neukirchen OT Adorf) ---
LATITUDE = 50.7725
LONGITUDE = 12.8860
MIN_SCORE = 60  # Mindest-Score für Kalendereintrag (grün)

# Katalogsammlung mit Typ-Klassifizierung:
# 'NB' = Narrowband / Schmalband (Emissionsnebel, Planetarische Nebel, SNR)
# 'BB' = Broadband / Breitband (Galaxien, Reflexionsnebel, Sternhaufen)
DSO_CATALOG = [
    # Galaxien & Sternhaufen (BB)
    {"cat": "M31", "name": "Andromeda-Galaxie", "dec": 41.2, "months": [8, 9, 10, 11, 12, 1], "type": "BB"},
    {"cat": "M33", "name": "Dreiecks-Galaxie", "dec": 30.6, "months": [9, 10, 11, 12, 1], "type": "BB"},
    {"cat": "M81 / M82", "name": "Bodes Galaxie & Zigarre", "dec": 69.1, "months": [12, 1, 2, 3, 4, 5], "type": "BB"},
    {"cat": "M51", "name": "Whirlpool-Galaxie", "dec": 47.2, "months": [2, 3, 4, 5, 6, 7], "type": "BB"},
    {"cat": "M101", "name": "Feuerrad-Galaxie", "dec": 54.4, "months": [3, 4, 5, 6, 7], "type": "BB"},
    {"cat": "M104", "name": "Sombrero-Galaxie", "dec": -11.6, "months": [3, 4, 5, 6], "type": "BB"},
    {"cat": "M106", "name": "Spiralgalaxie Canes Venatici", "dec": 47.3, "months": [2, 3, 4, 5, 6], "type": "BB"},
    {"cat": "M109", "name": "Spiralgalaxie Ursa Major", "dec": 53.4, "months": [2, 3, 4, 5, 6], "type": "BB"},
    {"cat": "M63", "name": "Sonnenblumen-Galaxie", "dec": 42.0, "months": [3, 4, 5, 6, 7], "type": "BB"},
    {"cat": "M74", "name": "Phantom-Galaxie", "dec": 15.8, "months": [9, 10, 11, 12, 1], "type": "BB"},
    {"cat": "NGC 7331", "name": "Deer Lick Gruppe", "dec": 34.4, "months": [8, 9, 10, 11, 12], "type": "BB"},
    {"cat": "NGC 891", "name": "Outer Line Galaxie", "dec": 42.4, "months": [9, 10, 11, 12, 1], "type": "BB"},
    {"cat": "NGC 2403", "name": "Spiralgalaxie Camelopardalis", "dec": 65.6, "months": [11, 12, 1, 2, 3, 4], "type": "BB"},
    {"cat": "M45", "name": "Plejaden (Reflexionsnebel)", "dec": 24.1, "months": [10, 11, 12, 1, 2], "type": "BB"},
    {"cat": "M78", "name": "Reflexionsnebel Orion", "dec": 0.1, "months": [12, 1, 2, 3], "type": "BB"},
    {"cat": "NGC 1333", "name": "Reflexionsnebel Perseus", "dec": 31.4, "months": [9, 10, 11, 12, 1], "type": "BB"},
    {"cat": "M13", "name": "Herkules-Kugelsternhaufen", "dec": 36.5, "months": [4, 5, 6, 7, 8, 9], "type": "BB"},
    {"cat": "M92", "name": "Kugelsternhaufen Herkules", "dec": 43.1, "months": [5, 6, 7, 8, 9], "type": "BB"},
    {"cat": "M3", "name": "Kugelsternhaufen Jagdhunde", "dec": 28.4, "months": [3, 4, 5, 6, 7], "type": "BB"},
    {"cat": "NGC 869 / 884", "name": "Doppelsternhaufen h & chi", "dec": 57.1, "months": [8, 9, 10, 11, 12, 1, 2], "type": "BB"},

    # Nebel-Objekte (NB - Schmalband-geeignet)
    {"cat": "NGC 7000", "name": "Nordamerika-Nebel", "dec": 44.4, "months": [5, 6, 7, 8, 9, 10], "type": "NB"},
    {"cat": "NGC 6992 / 6960", "name": "Schleiernebel (Veil)", "dec": 31.7, "months": [6, 7, 8, 9, 10, 11], "type": "NB"},
    {"cat": "NGC 6888", "name": "Crescent-Nebel", "dec": 38.4, "months": [6, 7, 8, 9, 10], "type": "NB"},
    {"cat": "IC 1396", "name": "Elefantenrüsselnebel", "dec": 57.5, "months": [7, 8, 9, 10, 11], "type": "NB"},
    {"cat": "IC 5146", "name": "Kokon-Nebel", "dec": 47.3, "months": [7, 8, 9, 10, 11], "type": "NB"},
    {"cat": "IC 1805", "name": "Herznebel", "dec": 61.5, "months": [8, 9, 10, 11, 12, 1], "type": "NB"},
    {"cat": "IC 1848", "name": "Seelennebel", "dec": 60.4, "months": [8, 9, 10, 11, 12, 1], "type": "NB"},
    {"cat": "NGC 281", "name": "Pacman-Nebel", "dec": 56.6, "months": [8, 9, 10, 11, 12], "type": "NB"},
    {"cat": "NGC 1499", "name": "Kaliforniennebel", "dec": 36.6, "months": [9, 10, 11, 12, 1, 2], "type": "NB"},
    {"cat": "M42 / M43", "name": "Orionnebel", "dec": -5.4, "months": [11, 12, 1, 2, 3], "type": "NB"},
    {"cat": "IC 434 / B33", "name": "Pferdekopfnebel", "dec": -2.5, "months": [11, 12, 1, 2, 3], "type": "NB"},
    {"cat": "M1", "name": "Krebsnebel", "dec": 22.0, "months": [11, 12, 1, 2, 3, 4], "type": "NB"},
    {"cat": "IC 405", "name": "Flammensternnebel", "dec": 34.4, "months": [11, 12, 1, 2, 3], "type": "NB"},
    {"cat": "NGC 2237", "name": "Rosettennebel", "dec": 5.0, "months": [12, 1, 2, 3, 4], "type": "NB"},
    {"cat": "M57", "name": "Ringnebel", "dec": 33.0, "months": [5, 6, 7, 8, 9, 10], "type": "NB"},
    {"cat": "M27", "name": "Hantelnebel", "dec": 22.7, "months": [5, 6, 7, 8, 9, 10], "type": "NB"},
    {"cat": "M97", "name": "Eulennebel", "dec": 55.0, "months": [2, 3, 4, 5, 6], "type": "NB"},
    {"cat": "M16", "name": "Adlernebel (Säulen)", "dec": -13.8, "months": [5, 6, 7, 8], "type": "NB"},
    {"cat": "M17", "name": "Omega- / Schwanennebel", "dec": -16.2, "months": [5, 6, 7, 8], "type": "NB"},
    {"cat": "M8", "name": "Lagunennebel", "dec": -24.4, "months": [6, 7, 8], "type": "NB"},
    {"cat": "M20", "name": "Trifidnebel", "dec": -23.0, "months": [6, 7, 8], "type": "NB"}
]

def calculate_astronomical_night(date_str, lat=LATITUDE, lon=LONGITUDE):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday
        
        gamma = (2 * math.pi / 365) * (day_of_year - 1)
        eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
        decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma) - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
        
        lat_rad = math.radians(lat)
        zenith = math.radians(108.0) # -18° Elevation
        
        cos_ha = (math.cos(zenith) - math.sin(lat_rad) * math.sin(decl)) / (math.cos(lat_rad) * math.cos(decl))
        
        if cos_ha > 1.0 or cos_ha < -1.0:
            return None, None
        
        ha_deg = math.degrees(math.acos(cos_ha))
        ha_minutes = ha_deg * 4.0
        
        solar_noon_utc = 720 - (4 * lon) - eqtime
        dusk_utc_min = solar_noon_utc + ha_minutes
        dawn_utc_min = solar_noon_utc - ha_minutes
        
        dusk_utc = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc) + timedelta(minutes=dusk_utc_min)
        dawn_utc = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=dawn_utc_min - 1440)
        
        return dusk_utc, dawn_utc
    except Exception:
        return None, None

def get_sorted_targets(month, narrowband_only=False):
    matched = []
    for t in DSO_CATALOG:
        if month in t['months']:
            # Wenn Schmalband-Nacht, nur Schmalband-Nebel ('NB') ausgeben
            if narrowband_only and t['type'] != 'NB':
                continue
            max_alt = round(90.0 - abs(LATITUDE - t['dec']))
            matched.append({"cat": t['cat'], "name": t['name'], "max_alt": max_alt})
            
    matched.sort(key=lambda x: x['max_alt'], reverse=True)
    formatted = [f"• {t['cat']} ({t['name']}) - Max. Höhe: {t['max_alt']}°" for t in matched]
    return formatted if formatted else ["• Keine passenden Objekte gelistet"]

def format_time_str(iso_str):
    if not iso_str or iso_str == "N/A" or len(iso_str) < 16:
        return "N/A"
    return iso_str[-5:]

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
            
        n_clouds = [clouds_hourly for k in night_indices]
        n_low = [clouds_low for k in night_indices] if clouds_low else n_clouds
        n_mid = [clouds_mid for k in night_indices] if clouds_mid else n_clouds
        n_high = [clouds_high for k in night_indices] if clouds_high else n_clouds
        
        n_humidity = [humidity_hourly for k in night_indices]
        n_precip_prob = [precip_prob_hourly for k in night_indices]
        n_precip = [precip_hourly for k in night_indices]
        
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
        
        weighted_cloud = (avg_low * 0.5) + (avg_mid * 0.3) + (avg_high * 0.2)
        cloud_score = (100 - weighted_cloud) * 0.75
        
        # SCHMALBAND-FILTER-LOGIK: Bei klarem Himmel und Mond > 30% Schmalband-Objektfilter aktivieren
        is_narrowband_night = (weighted_cloud < 15 and moon_illumination > 30)
        
        if is_narrowband_night:
            effective_moon_illumination = moon_illumination * 0.25
            narrowband_note = " 🎯 Ideal für Schmalband/Filter"
        else:
            effective_moon_illumination = moon_illumination
            narrowband_note = ""
            
        moon_score = (100 - effective_moon_illumination) * 0.15
        humidity_score = (100 - max(0, avg_humidity - 70) * 3.33) * 0.10
        precip_penalty = (max_precip_prob / 100.0) * 30
        
        total_score = max(0, min(100, int(cloud_score + moon_score + humidity_score - precip_penalty)))
        
        if total_score < MIN_SCORE:
            continue
            
        date_str = times_hourly[start_idx][:10]
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        summary = f"🔭 🟢 Deep Sky: {total_score}%"
        
        dusk_utc, dawn_utc = calculate_astronomical_night(date_str)
        
        sunset_raw = sunsets[day] if day < len(sunsets) else ""
        sunrise_raw = sunrises[day+1] if (day+1) < len(sunrises) else (sunrises[day] if day < len(sunrises) else "")
        sunset_time = format_time_str(sunset_raw)
        sunrise_time = format_time_str(sunrise_raw)
        
        if dusk_utc and dawn_utc:
            astro_str = f"{dusk_utc.strftime('%H:%M')} - {dawn_utc.strftime('%H:%M')} UTC"
            dt_start_ics = dusk_utc.strftime('%Y%m%dT%H%M%SZ')
            dt_end_ics = dawn_utc.strftime('%Y%m%dT%H%M%SZ')
        else:
            astro_str = f"Sommernacht (Sonnenuntergang: {sunset_time} - {sunrise_time})"
            dt_start_ics = None
            dt_end_ics = None

        # Gefilterte Objektliste abrufen
        targets = get_sorted_targets(dt_obj.month, narrowband_only=is_narrowband_night)
        targets_str = "\\n".join(targets)
        
        dew_warning = " ⚠️ (Tau-Risiko)" if avg_humidity >= 85 else ""
        precip_str = f"{max_precip_prob}% ({total_precip:.1f} mm)" if max_precip_prob > 0 else "0% (Trocken)"
        
        section_header = "Sichtbare Schmalband-Objekte (Nebel):" if is_narrowband_night else "Sichtbare Objekte (sortiert nach Zenithöhe):"
        
        description = (
            f"Astro-Dunkelheit (Sonne <= -18°): {astro_str}\\n"
            f"Bewölkung (Nacht): Tiefe {int(avg_low)}% | Mid {int(avg_mid)}% | High {int(avg_high)}% (Schnitt: {int(avg_cloud)}%)\\n"
            f"Mond: ~{moon_illumination}%{narrowband_note} | Aufgang: {m_rise} | Untergang: {m_set}\\n"
            f"Niederschlag: {precip_str}\\n"
            f"Luftfeuchtigkeit: {int(avg_humidity)}%{dew_warning}\\n\\n"
            f"{section_header}\\n"
            f"{targets_str}\\n\\n"
            f"Erstellt via Open-Meteo Astro API"
        )
        
        if dt_start_ics and dt_end_ics:
            dt_lines = f"DTSTART:{dt_start_ics}\nDTEND:{dt_end_ics}"
        else:
            dt_start = date_str.replace("-", "")
            dt_lines = f"DTSTART;VALUE=DATE:{dt_start}"
            
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
    print("Erfolgreich generiert mit dynamischem Objektfilter!")

if __name__ == "__main__":
    generate_ics()
