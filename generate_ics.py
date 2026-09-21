import json
import urllib.request
import ssl
from datetime import datetime, timezone

# --- KOORDINATEN ---
LATITUDE = 50.7725
LONGITUDE = 12.8860
LOCATION_NAME = "Neukirchen OT Adorf"

def generate_ics():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&hourly=cloud_cover&forecast_days=7&timezone=auto"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"Lade Daten von Open-Meteo...")
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))

    hourly = data.get("hourly", {})
    clouds_hourly = hourly.get("cloud_cover", [])
    times_hourly = hourly.get("time", [])

    events = []
    for day in range(7):
        start_idx = day * 24
        end_idx = start_idx + 24
        
        day_clouds = clouds_hourly[start_idx:end_idx]
        if not day_clouds:
            continue
            
        avg_cloud = sum(day_clouds) / len(day_clouds)
        score = max(0, min(100, int(100 * (1 - (avg_cloud / 100.0)))))
        
        date_str = times_hourly[start_idx][:10]
        status_icon = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        
        summary = f"{status_icon} Deep Sky Score: {score}% (Wolken: {int(avg_cloud)}%)"
        description = (
            f"Ort: {LOCATION_NAME}\\n"
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
    print("deepsky.ics wurde erfolgreich erstellt!")

if __name__ == "__main__":
    generate_ics()
