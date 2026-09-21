import json
from datetime import datetime, timezone

LOCATION_NAME = "Neukirchen OT Adorf"

def generate_ics():
    print("Lese weather.json ein...")
    with open("weather.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
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
            f"Erstellt via Open-Meteo API"
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
