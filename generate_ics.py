import json
import urllib.request
import urllib.parse
import ssl
import sys
from datetime import datetime, timezone

# --- DEINE KOORDINATEN ---
LATITUDE = 50.7725   # Breitengrad
LONGITUDE = 12.8860  # Längengrad
LOCATION_NAME = "Neukirchen OT Adorf"

def fetch_weather():
    # urllib.parse.urlencode sorgt für eine 100% fehlerfreie URL-Codierung
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "cloud_cover",
        "daily": "sunrise,sunset",
        "timezone": "UTC"
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx) as response:
        return json.loads(response.read().decode("utf-8"))

def generate_ics():
    print("Starte Wetter-Abruf...")
    data = fetch_weather()
    daily = data.get("daily", {})
    hourly = data.get("hourly", {})
    
    times = daily.get("time", [])
    sunrises = daily.get("sunrise", [])
    sunsets = daily.get("sunset", [])
    clouds_hourly = hourly.get("cloud_cover", [])
    
    events = []
    
    for i in range(len(times)):
        date_str = times[i]
        
        sunset_val = sunsets[i] if i < len(sunsets) else ""
        sunrise_val = sunrises[i] if i < len(sunrises) else ""
        
        sunset_time = sunset_val[-5:] if len(sunset_val) >= 5 else "N/A"
        sunrise_time = sunrise_val[-5:] if len(sunrise_val) >= 5 else "N/A"
        
        clouds = clouds_hourly[i * 24:(i + 1) * 24]
        avg_cloud = sum(clouds) / len(clouds) if clouds else 50
        
        score = max(0, min(100, int(100 * (1 - (avg_cloud / 100.0)))))
        status_icon = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        
        summary = f"{status_icon} Deep Sky Score: {score}% (Wolken: {int(avg_cloud)}%)"
        description = (
            f"Ort: {LOCATION_NAME}\\n"
            f"Sonnenuntergang: {sunset_time} UTC | Sonnenaufgang: {sunrise_time} UTC\\n"
            f"Bewölkung im Schnitt: {int(avg_cloud)}%\\n"
            f"Erstellt via Open-Meteo"
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
    print("Erfolgreich ausgeführt und deepsky.ics erstellt!")

if __name__ == "__main__":
    generate_ics()
