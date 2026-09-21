import json
import urllib.request
import sys
from datetime import datetime, timezone

# --- DEINE KOORDINATEN ---
LATITUDE = 50.7725   # Breitengrad
LONGITUDE = 12.8860  # Längengrad
LOCATION_NAME = "Home"

def fetch_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"hourly=cloud_cover&"
        f"daily=sunrise,sunset&"
        f"forecast_days=7&timezone=Europe%2FBerlin"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (AstroCalendarBot)'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Fehler beim API-Abruf: {e}", file=sys.stderr)
        raise e

def calculate_score(cloud_cover):
    cloud_penalty = cloud_cover / 100.0
    score = int(100 * (1 - cloud_penalty))
    return max(0, min(100, score))

def generate_ics():
    print("Starte Datenabruf von Open-Meteo...")
    data = fetch_weather()
    daily = data.get('daily', {})
    hourly = data.get('hourly', {})
    
    events = []
    times = daily.get('time', [])
    sunrises = daily.get('sunrise', [])
    sunsets = daily.get('sunset', [])
    clouds_hourly = hourly.get('cloud_cover', [])
    
    for i in range(len(times)):
        date_str = times[i]
        sunset = sunsets[i] if i < len(sunsets) and sunsets[i] else "N/A"
        sunrise = sunrises[i+1] if (i+1) < len(sunrises) and sunrises[i+1] else "N/A"
        
        clouds = clouds_hourly[i * 24:(i + 1) * 24]
        avg_cloud = sum(clouds) / len(clouds) if clouds else 50
        
        score = calculate_score(avg_cloud)
        
        status_icon = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        
        sunset_time = sunset[-5:] if len(sunset) >= 5 else sunset
        sunrise_time = sunrise[-5:] if len(sunrise) >= 5 else sunrise
        
        summary = f"{status_icon} Deep Sky Score: {score}% (Wolken: {int(avg_cloud)}%)"
        description = (
            f"Ort: {LOCATION_NAME}\\n"
            f"Nachtfenster (Sonnenunter-/aufgang): {sunset_time} - {sunrise_time} Uhr\\n"
            f"Bewölkung im Schnitt: {int(avg_cloud)}%\\n"
            f"Erstellt automatisch via Open-Meteo"
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
    print("deepsky.ics erfolgreich erstellt!")

if __name__ == "__main__":
    generate_ics()
