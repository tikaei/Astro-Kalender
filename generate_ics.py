import json
import urllib.request
from datetime import datetime, timezone

# --- DEINE KOORDINATEN (Hier deinen Wohnort eintragen) ---
LATITUDE = 50.7725   # Breitengrad deines Wohnorts
LONGITUDE = 12.8860  # Längengrad deines Wohnorts
LOCATION_NAME = "Home"

def fetch_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,relative_humidity_2m&"
        f"daily=astronomical_dusk,astronomical_dawn,moon_phase&"
        f"forecast_days=7&timezone=Europe%2FBerlin"
    )
    req = urllib.request.urlopen(url)
    return json.loads(req.read().decode('utf-8'))

def calculate_score(cloud_cover, moon_phase):
    # Mondphase: 0 = Neumond (ideal), 0.5 = Halbmond, 1 = Vollmond
    moon_penalty = abs(moon_phase - 0.5) * 2
    cloud_penalty = cloud_cover / 100.0
    
    score = int(100 * (1 - (0.6 * cloud_penalty + 0.4 * moon_penalty)))
    return max(0, min(100, score))

def generate_ics():
    data = fetch_weather()
    daily = data.get('daily', {})
    
    events = []
    
    for i in range(len(daily.get('time', []))):
        date_str = daily['time'][i]
        dusk = daily['astronomical_dusk'][i]
        dawn = daily['astronomical_dawn'][i]
        moon_phase = daily['moon_phase'][i]
        
        clouds = data['hourly']['cloud_cover'][i * 24:(i + 1) * 24]
        avg_cloud = sum(clouds) / len(clouds) if clouds else 50
        
        score = calculate_score(avg_cloud, moon_phase)
        
        status_icon = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        
        summary = f"{status_icon} Deep Sky Score: {score}% (Wolken: {int(avg_cloud)}%)"
        description = (
            f"Ort: {LOCATION_NAME}\\n"
            f"Astronomische Nacht: {dusk[-5:]} - {dawn[-5:]} Uhr\\n"
            f"Bewölkung (Schnitt): {int(avg_cloud)}%\\n"
            f"Mondphase Wert (0=Neumond, 1=Vollmond): {moon_phase}\\n"
            f"Erstellt automatisch via Open-Meteo API"
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

if __name__ == "__main__":
    generate_ics()
