import json
import urllib.request
import ssl
from datetime import datetime, timezone

# --- KOORDINATEN (Neukirchen OT Adorf) ---
LATITUDE = 50.7725
LONGITUDE = 12.8860

# Katalog-Objekte für ~51° N (Sichtbarkeit im Zeitfenster 20:00 - 03:00 Uhr nach Monat)
DSO_TARGETS = [
    {"cat": "M31", "name": "Andromeda-Galaxie", "months": [8, 9, 10, 11, 12]},
    {"cat": "M33", "name": "Dreiecks-Galaxie", "months": [9, 10, 11, 12, 1]},
    {"cat": "M42 / M43", "name": "Orionnebel", "months": [11, 12, 1, 2, 3]},
    {"cat": "M45", "name": "Plejaden", "months": [10, 11, 12, 1, 2]},
    {"cat": "NGC 7000", "name": "Nordamerika-Nebel", "months": [6, 7, 8, 9, 10]},
    {"cat": "IC 1396", "name": "Elefantenrüsselnebel", "months": [7, 8, 9, 10, 11]},
    {"cat": "IC 1805", "name": "Herznebel", "months": [9, 10, 11, 12, 1]},
    {"cat": "IC 1848", "name": "Seelennebel", "months": [9, 10, 11, 12, 1]},
    {"cat": "NGC 6992 / 6960", "name": "Schleiernebel (Veil)", "months": [6, 7, 8, 9, 10]},
    {"cat": "M27", "name": "Hantelnebel", "months": [6, 7, 8, 9, 10]},
    {"cat": "M57", "name": "Ringnebel", "months": [5, 6, 7, 8, 9]},
    {"cat": "M81 / M82", "name": "Bodes Galaxie & Zigarre", "months": [1, 2, 3, 4, 5]},
    {"cat": "M51", "name": "Whirlpool-Galaxie", "months": [2, 3, 4, 5, 6]},
    {"cat": "NGC 2237", "name": "Rosettennebel", "months": [12, 1, 2, 3]},
    {"cat": "IC 434 / B33", "name": "Pferdekopfnebel", "months": [11, 12, 1, 2]},
    {"cat": "NGC 1499", "name": "Kaliforniennebel", "months": [10, 11, 12, 1, 2]},
    {"cat": "NGC 869 / 884", "name": "Doppelsternhaufen h & chi", "months": [8, 9, 10, 11, 12, 1]}
]

def get_recommended_targets(month):
    matches = [f"• {t['cat']} ({t['name']})" for t in DSO_TARGETS if month in t['months']]
    return matches[:5] if matches else ["• Keine speziellen Favoriten gelistet"]

def generate_ics():
    # Wetter, Bewölkung, Luftfeuchtigkeit, Niederschlag, Tag/Nacht & Mondphase abrufen
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"hourly=cloud_cover,relative_humidity_2m,precipitation_probability,precipitation,is_day&"
        f"daily=moon_phase&"
        f"forecast_days=7&timezone=auto"
    )
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("Lade Wetter-, Niederschlags- und Astrodaten...")
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    
    clouds_hourly = hourly.get("cloud_cover", [])
    humidity_hourly = hourly.get("relative_humidity_2m", [])
    precip_prob_hourly = hourly.get("precipitation_probability", [])
    precip_hourly = hourly.get("precipitation", [])
    is_day_hourly = hourly.get("is_day", [])
    times_hourly = hourly.get("time", [])
    moon_phases = daily.get("moon_phase", [])

    events = []

    for day in range(7):
        start_idx = day * 24
        end_idx = start_idx + 24
        
        # Auswertung ausschließlich für die Nachtstunden (is_day == 0)
        night_indices = [k for k in range(start_idx, end_idx) if is_day_hourly[k] == 0]
        if not night_indices:
            night_indices = list(range(start_idx, end_idx))
            
        night_clouds = [clouds_hourly[k] for k in night_indices]
        night_humidity = [humidity_hourly[k] for k in night_indices]
        night_precip_prob = [precip_prob_hourly[k] for k in night_indices]
        night_precip = [precip_hourly[k] for k in night_indices]
        
        avg_night_cloud = sum(night_clouds) / len(night_clouds) if night_clouds else 50
        avg_night_humidity = sum(night_humidity) / len(night_humidity) if night_humidity else 50
        max_precip_prob = max(night_precip_prob) if night_precip_prob else 0
        total_precip = sum(night_precip) if night_precip else 0.0
        
        # Mondphase
        moon_phase_val = moon_phases[day] if day < len(moon_phases) else 0.5
        moon_illumination = int((1 - abs(moon_phase_val - 0.5) * 2) * 100)
        
        # Score-Berechnung
        cloud_score = (100 - avg_night_cloud) * 0.70
        moon_score = (100 - moon_illumination) * 0.20
        humidity_score = (100 - max(0, avg_night_humidity - 70) * 3.33) * 0.10
        precip_penalty = (max_precip_prob / 100.0) * 30
        
        total_score = max(0, min(100, int(cloud_score + moon_score + humidity_score - precip_penalty)))
        
        date_str = times_hourly[start_idx][:10]
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        status_icon = "🟢" if total_score >= 70 else "🟡" if total_score >= 45 else "🔴"
        
        # 1. Kompakter Titel
        summary = f"🔭 {status_icon} Deep Sky: {total_score}%"
        
        # Empfehlungen für den Monat
        targets = get_recommended_targets(dt_obj.month)
        targets_str = "\\n".join(targets)
        
        dew_warning = " ⚠️ (Tau-Risiko)" if avg_night_humidity >= 85 else ""
        precip_str = f"{max_precip_prob}% ({total_precip:.1f} mm)" if max_precip_prob > 0 else "0% (Trocken)"
        
        # 2. Ereignisbeschreibung
        description = (
            f"Bewölkung (Nacht): {int(avg_night_cloud)}%\\n"
            f"Niederschlag: {precip_str}\\n"
            f"Mondbeleuchtung: ~{moon_illumination}%\\n"
            f"Luftfeuchtigkeit: {int(avg_night_humidity)}%{dew_warning}\\n\\n"
            f"Empfohlene Objekte (20:00-03:00 Uhr):\\n"
            f"{targets_str}\\n\\n"
            f"Erstellt via Open-Meteo Astro API"
        )
        
        dt_start = date_str.replace("-", "")
        
        events.append(f"""BEGIN:VEVENT
UID:astro-{date_str}@deepsky
DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}
DTSTART;VALUE=DATE:{dt_start}
SUMMARY:{summary}
DESCRIPTION:{description}
END:VEVENT""")

    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//DeepSkyForecast//DE\nX-WR-CALNAME:Deep Sky Vorhersage\n" + "\n".join(events) + "\nEND:VCALENDAR"
    
    with open("deepsky.ics", "w", encoding="utf-8") as f:
        f.write(ics_content)
    print("Optimierte deepsky.ics erfolgreich erstellt!")

if __name__ == "__main__":
    generate_ics()
