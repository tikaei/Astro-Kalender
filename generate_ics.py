import json
import urllib.request
import ssl
from datetime import datetime, timezone

# --- KOORDINATEN ---
LATITUDE = 50.7725
LONGITUDE = 12.8860
LOCATION_NAME = "Neukirchen OT Adorf"

def generate_ics():
    # Abruf von Bewölkung, Luftfeuchtigkeit, Tag/Nacht-Kennung und Mondphase
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"hourly=cloud_cover,relative_humidity_2m,is_day&"
        f"daily=moon_phase&"
        f"forecast_days=7&timezone=auto"
    )
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("Lade erweiterte Astro-Wetterdaten...")
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    
    clouds_hourly = hourly.get("cloud_cover", [])
    humidity_hourly = hourly.get("relative_humidity_2m", [])
    is_day_hourly = hourly.get("is_day", [])
    times_hourly = hourly.get("time", [])
    moon_phases = daily.get("moon_phase", [])

    events = []

    for day in range(7):
        start_idx = day * 24
        end_idx = start_idx + 24
        
        # Nur Nachtstunden herausfiltern (is_day == 0)
        night_clouds = [clouds_hourly[k] for k in range(start_idx, end_idx) if is_day_hourly[k] == 0]
        night_humidity = [humidity_hourly[k] for k in range(start_idx, end_idx) if is_day_hourly[k] == 0]
        
        # Fallback, falls in Polarnächten/Sommer keine Nachtstunden erkannt werden
        if not night_clouds:
            night_clouds = clouds_hourly[start_idx:end_idx]
            night_humidity = humidity_hourly[start_idx:end_idx]
            
        avg_night_cloud = sum(night_clouds) / len(night_clouds) if night_clouds else 50
        avg_night_humidity = sum(night_humidity) / len(night_humidity) if night_humidity else 50
        
        # Mondphase (0 = Neumond, 0.5 = Vollmond) -> Errechnung der Mondbeleuchtung in %
        moon_phase_val = moon_phases[day] if day < len(moon_phases) else 0.5
        moon_illumination = int((1 - abs(moon_phase_val - 0.5) * 2) * 100)
        
        # Deep Sky Score Berechnung: 70% Gewichtung Wolken, 20% Mond, 10% Luftfeuchtigkeit
        cloud_score = (100 - avg_night_cloud) * 0.70
        moon_score = (100 - moon_illumination) * 0.20
        humidity_score = (100 - max(0, avg_night_humidity - 70) * 3.33) * 0.10
        
        total_score = max(0, min(100, int(cloud_score + moon_score + humidity_score)))
        
        date_str = times_hourly[start_idx][:10]
        status_icon = "🟢" if total_score >= 70 else "🟡" if total_score >= 45 else "🔴"
        
        # Zusatzwarnung bei hoher Luftfeuchtigkeit
        dew_warning = "⚠️ Hohes Tau-Risiko!" if avg_night_humidity >= 85 else "Gering"
        
        summary = f"{status_icon} Deep Sky: {total_score}% (Nachtwolken: {int(avg_night_cloud)}%)"
        description = (
            f"Ort: {LOCATION_NAME}\\n"
            f"Bewölkung (Nacht): {int(avg_night_cloud)}%\\n"
            f"Mondbeleuchtung: ~{moon_illumination}%\\n"
            f"Luftfeuchtigkeit (Nacht): {int(avg_night_humidity)}% ({dew_warning})\\n"
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

    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//DeepSkyForecast//DE\nX-WR-CALNAME:Deep Sky Fotografie Vorhersage\n" + "\n".join(events) + "\nEND:VCALENDAR"
    
    with open("deepsky.ics", "w", encoding="utf-8") as f:
        f.write(ics_content)
    print("Optimierte deepsky.ics erfolgreich erstellt!")

if __name__ == "__main__":
    generate_ics()
