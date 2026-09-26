import json
import urllib.request
import urllib.error
import ssl
import sys
import math
from datetime import datetime, timezone, timedelta

# Import des unantastbaren ICS-Formatierers
import ics_builder

# --- KOORDINATEN (Neukirchen OT Adorf) ---
LATITUDE = 50.7725
LONGITUDE = 12.8860

# Katalog mit DWARF 3 Filter-Klassifizierung (Nördliche Hemisphäre)
DSO_CATALOG = [
    # --- STERNHAUFEN (DWARF 3 Filter: Astro) ---
    {"cat": "NGC 457", "name": "Eulenhaufen / ET-Cluster", "ra": 1.33, "dec": 58.3, "months": [8, 9, 10, 11, 12, 1], "type": "cluster"},
    {"cat": "NGC 869 / 884", "name": "Doppelsternhaufen h & chi", "ra": 2.32, "dec": 57.1, "months": [8, 9, 10, 11, 12, 1, 2], "type": "cluster"},
    {"cat": "M13", "name": "Herkules-Kugelsternhaufen", "ra": 16.69, "dec": 36.5, "months": [4, 5, 6, 7, 8, 9, 10], "type": "cluster"},
    {"cat": "M92", "name": "Kugelsternhaufen Herkules", "ra": 17.28, "dec": 43.1, "months": [4, 5, 6, 7, 8, 9, 10], "type": "cluster"},
    {"cat": "M3", "name": "Kugelsternhaufen Jagdhunde", "ra": 13.71, "dec": 28.4, "months": [2, 3, 4, 5, 6, 7, 8], "type": "cluster"},
    {"cat": "M5", "name": "Kugelsternhaufen Schlange", "ra": 15.31, "dec": 2.0, "months": [3, 4, 5, 6, 7], "type": "cluster"},
    {"cat": "M15", "name": "Kugelsternhaufen Pegasus", "ra": 21.50, "dec": 12.2, "months": [7, 8, 9, 10, 11, 12], "type": "cluster"},
    {"cat": "M2", "name": "Kugelsternhaufen Wassermann", "ra": 21.56, "dec": -0.8, "months": [7, 8, 9, 10, 11], "type": "cluster"},
    {"cat": "M11", "name": "Wildenten-Haufen", "ra": 18.85, "dec": -9.4, "months": [5, 6, 7, 8, 9], "type": "cluster"},
    {"cat": "M34", "name": "Offener Haufen Perseus", "ra": 2.70, "dec": 42.8, "months": [8, 9, 10, 11, 12, 1], "type": "cluster"},
    {"cat": "M35", "name": "Offener Haufen Zwillinge", "ra": 6.15, "dec": 24.3, "months": [10, 11, 12, 1, 2, 3, 4], "type": "cluster"},
    {"cat": "M36", "name": "Offener Haufen Fuhrmann", "ra": 5.60, "dec": 34.1, "months": [10, 11, 12, 1, 2, 3, 4], "type": "cluster"},
    {"cat": "M37", "name": "Offener Haufen Fuhrmann", "ra": 5.87, "dec": 32.5, "months": [10, 11, 12, 1, 2, 3, 4], "type": "cluster"},
    {"cat": "M38", "name": "Offener Haufen Fuhrmann", "ra": 5.48, "dec": 35.8, "months": [10, 11, 12, 1, 2, 3, 4], "type": "cluster"},
    {"cat": "NGC 7789", "name": "Caroline's Rose", "ra": 23.95, "dec": 56.7, "months": [7, 8, 9, 10, 11, 12, 1], "type": "cluster"},

    # --- EMISSIONSNEBEL / PLANETARISCHE NEBEL (DWARF 3 Filter: Duo-Band) ---
    {"cat": "NGC 7000", "name": "Nordamerika-Nebel", "ra": 20.98, "dec": 44.4, "months": [5, 6, 7, 8, 9, 10, 11], "type": "narrowband"},
    {"cat": "IC 5070", "name": "Pelikannebel", "ra": 20.85, "dec": 44.4, "months": [5, 6, 7, 8, 9, 10, 11], "type": "narrowband"},
    {"cat": "NGC 6992 / 6960", "name": "Schleiernebel (Veil)", "ra": 20.93, "dec": 31.7, "months": [6, 7, 8, 9, 10, 11], "type": "narrowband"},
    {"cat": "IC 1396", "name": "Elefantenrüsselnebel", "ra": 21.60, "dec": 57.5, "months": [6, 7, 8, 9, 10, 11, 12], "type": "narrowband"},
    {"cat": "IC 1805", "name": "Herznebel", "ra": 2.55, "dec": 61.5, "months": [8, 9, 10, 11, 12, 1, 2], "type": "narrowband"},
    {"cat": "IC 1848", "name": "Seelennebel", "ra": 2.85, "dec": 60.4, "months": [8, 9, 10, 11, 12, 1, 2], "type": "narrowband"},
    {"cat": "NGC 281", "name": "Pacman-Nebel", "ra": 0.88, "dec": 56.6, "months": [8, 9, 10, 11, 12, 1], "type": "narrowband"},
    {"cat": "NGC 6888", "name": "Crescent-Nebel", "ra": 20.20, "dec": 38.4, "months": [5, 6, 7, 8, 9, 10, 11], "type": "narrowband"},
    {"cat": "NGC 1499", "name": "Kaliforniennebel", "ra": 4.05, "dec": 36.6, "months": [9, 10, 11, 12, 1, 2], "type": "narrowband"},
    {"cat": "NGC 2237", "name": "Rosettennebel", "ra": 6.53, "dec": 5.0, "months": [11, 12, 1, 2, 3, 4], "type": "narrowband"},
    {"cat": "IC 434 / B33", "name": "Pferdekopfnebel", "ra": 5.68, "dec": -2.5, "months": [10, 11, 12, 1, 2, 3], "type": "narrowband"},
    {"cat": "NGC 2359", "name": "Thors Helm", "ra": 7.31, "dec": -13.2, "months": [11, 12, 1, 2, 3], "type": "narrowband"},
    {"cat": "NGC 7635", "name": "Blasennebel (Bubble)", "ra": 23.35, "dec": 61.2, "months": [7, 8, 9, 10, 11, 12, 1], "type": "narrowband"},
    {"cat": "NGC 2174", "name": "Affenkopfnebel", "ra": 6.16, "dec": 20.8, "months": [11, 12, 1, 2, 3, 4], "type": "narrowband"},
    {"cat": "M27", "name": "Hantelnebel", "ra": 19.99, "dec": 22.7, "months": [5, 6, 7, 8, 9, 10, 11], "type": "narrowband"},
    {"cat": "M57", "name": "Ringnebel", "ra": 18.89, "dec": 33.0, "months": [5, 6, 7, 8, 9, 10, 11], "type": "narrowband"},
    {"cat": "M97", "name": "Eulennebel", "ra": 11.25, "dec": 55.0, "months": [1, 2, 3, 4, 5, 6], "type": "narrowband"},
    {"cat": "NGC 7293", "name": "Helixnebel", "ra": 22.49, "dec": -20.8, "months": [8, 9, 10, 11], "type": "narrowband"},
    {"cat": "Sh2-157", "name": "Hummernebel (Lobster)", "ra": 23.26, "dec": 60.0, "months": [7, 8, 9, 10, 11, 12, 1], "type": "narrowband"},

    # --- HYBRID (DWARF 3 Filter: Duo-Band oder Astro) ---
    {"cat": "M42 / M43", "name": "Orionnebel", "ra": 5.59, "dec": -5.4, "months": [10, 11, 12, 1, 2, 3, 4], "type": "hybrid"},
    {"cat": "IC 405", "name": "Flammensternnebel", "ra": 5.27, "dec": 34.4, "months": [10, 11, 12, 1, 2, 3, 4], "type": "hybrid"},
    {"cat": "M1", "name": "Krebsnebel", "ra": 5.58, "dec": 22.0, "months": [10, 11, 12, 1, 2, 3, 4], "type": "hybrid"},
    {"cat": "NGC 2024", "name": "Flammennebel Orion", "ra": 5.69, "dec": -1.9, "months": [10, 11, 12, 1, 2, 3], "type": "hybrid"},

    # --- GALAXIEN, REFLEXIONS- & DUNKELNEBEL (DWARF 3 Filter: Astro) ---
    {"cat": "M31", "name": "Andromeda-Galaxie", "ra": 0.71, "dec": 41.2, "months": [8, 9, 10, 11, 12, 1], "type": "broadband"},
    {"cat": "M33", "name": "Dreiecks-Galaxie", "ra": 1.56, "dec": 30.6, "months": [8, 9, 10, 11, 12, 1], "type": "broadband"},
    {"cat": "M45", "name": "Plejaden (Reflexion)", "ra": 3.79, "dec": 24.1, "months": [9, 10, 11, 12, 1, 2, 3], "type": "broadband"},
    {"cat": "IC 5146", "name": "Kokon-Nebel (B168)", "ra": 21.89, "dec": 47.3, "months": [6, 7, 8, 9, 10, 11, 12], "type": "broadband"},
    {"cat": "NGC 7023", "name": "Irisnebel", "ra": 21.03, "dec": 68.2, "months": [6, 7, 8, 9, 10, 11, 12, 1], "type": "broadband"},
    {"cat": "NGC 1333", "name": "Reflexionsnebel Perseus", "ra": 3.49, "dec": 31.4, "months": [8, 9, 10, 11, 12, 1, 2], "type": "broadband"},
    {"cat": "M78", "name": "Reflexionsnebel Orion", "ra": 5.78, "dec": 0.1, "months": [11, 12, 1, 2, 3, 4], "type": "broadband"},
    {"cat": "M51", "name": "Whirlpool-Galaxie", "ra": 13.50, "dec": 47.2, "months": [1, 2, 3, 4, 5, 6, 7], "type": "broadband"},
    {"cat": "M81 / M82", "name": "Bodes Galaxie & Zigarre", "ra": 9.92, "dec": 69.1, "months": [11, 12, 1, 2, 3, 4, 5, 6], "type": "broadband"},
    {"cat": "M101", "name": "Feuerrad-Galaxie", "ra": 14.05, "dec": 54.4, "months": [2, 3, 4, 5, 6, 7, 8], "type": "broadband"},
    {"cat": "M104", "name": "Sombrero-Galaxie", "ra": 12.66, "dec": -11.6, "months": [2, 3, 4, 5, 6], "type": "broadband"},
    {"cat": "NGC 6946", "name": "Supernova-Galaxie", "ra": 20.58, "dec": 60.1, "months": [6, 7, 8, 9, 10, 11, 12], "type": "broadband"},
    {"cat": "NGC 7331", "name": "Deer Lick Gruppe", "ra": 22.62, "dec": 34.4, "months": [7, 8, 9, 10, 11, 12], "type": "broadband"},
    {"cat": "M63", "name": "Sonnenblumen-Galaxie", "ra": 13.26, "dec": 42.0, "months": [2, 3, 4, 5, 6, 7, 8], "type": "broadband"},
    {"cat": "M106", "name": "Spiralgalaxie Canes Venatici", "ra": 12.31, "dec": 47.3, "months": [1, 2, 3, 4, 5, 6, 7], "type": "broadband"},
    {"cat": "M109", "name": "Spiralgalaxie Ursa Major", "ra": 11.96, "dec": 53.4, "months": [1, 2, 3, 4, 5, 6], "type": "broadband"},
    {"cat": "NGC 891", "name": "Outer Line Galaxie", "ra": 2.38, "dec": 42.4, "months": [8, 9, 10, 11, 12, 1], "type": "broadband"},
    {"cat": "M74", "name": "Phantom-Galaxie", "ra": 1.61, "dec": 15.8, "months": [8, 9, 10, 11, 12, 1], "type": "broadband"},
    {"cat": "NGC 2403", "name": "Spiralgalaxie Camelopardalis", "ra": 7.61, "dec": 65.6, "months": [10, 11, 12, 1, 2, 3, 4, 5], "type": "broadband"},
    {"cat": "M65 / M66", "name": "Leo-Triplett Galaxien", "ra": 11.33, "dec": 13.1, "months": [1, 2, 3, 4, 5], "type": "broadband"}
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
        dawn_utc = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc) + timedelta(days=1, minutes=dawn_utc_min)
        return dusk_utc, dawn_utc
    except Exception:
        return None, None

def calculate_transit_time_str(date_str, ra_hours, lon=LONGITUDE):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    Y, M, D = dt.year, dt.month, dt.day
    if M <= 2:
        Y -= 1
        M += 12
    A = math.floor(Y / 100)
    B = 2 - A + math.floor(A / 4)
    JD0 = math.floor(365.25 * (Y + 4716)) + math.floor(30.6001 * (M + 1)) + D + B - 1524.5
    
    D0 = JD0 - 2451545.0
    T = D0 / 36525.0
    gmst0 = (100.46061837 + 36000.770053608 * T + 0.000387933 * T**2 - T**3 / 38710000.0) % 360.0
    gmst0_hours = gmst0 / 15.0
    
    lst0_hours = (gmst0_hours + lon / 15.0) % 24.0
    diff = (ra_hours - lst0_hours) % 24.0
    transit_utc_hours = diff * 0.99726957
    
    transit_dt_utc = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc) + timedelta(hours=transit_utc_hours)
    
    m_last_sun = 31 - (datetime(dt.year, 3, 31).weekday() + 1) % 7
    o_last_sun = 31 - (datetime(dt.year, 10, 31).weekday() + 1) % 7
    dst_start = datetime(dt.year, 3, m_last_sun, 2, 0, tzinfo=timezone.utc)
    dst_end = datetime(dt.year, 10, o_last_sun, 3, 0, tzinfo=timezone.utc)
    
    is_dst = dst_start <= transit_dt_utc < dst_end
    local_offset = timedelta(hours=2 if is_dst else 1)
    
    transit_dt_local = transit_dt_utc + local_offset
    return transit_dt_local.strftime("%H:%M")

def get_sorted_targets(date_str, month, moon_illumination):
    matched = []
    for t in DSO_CATALOG:
        if month in t['months']:
            max_alt = round(90.0 - abs(LATITUDE - t['dec']))
            if max_alt > 10:
                transit_time = calculate_transit_time_str(date_str, t['ra'])
                obj_type = t.get("type", "broadband")
                
                # Explizite DWARF 3 Filter-Zuweisung
                if moon_illumination >= 50:
                    if obj_type == "narrowband":
                        rec_tag = "[🟢 DWARF 3: Duo-Band Filter]"
                        priority = 1
                    elif obj_type == "hybrid":
                        rec_tag = "[🟡 DWARF 3: Duo-Band oder Astro]"
                        priority = 2
                    elif obj_type == "cluster":
                        rec_tag = "[🟡 DWARF 3: Astro Filter (Mond ok)]"
                        priority = 3
                    else: # broadband
                        rec_tag = "[🔴 DWARF 3: Astro Filter (Vollmond-Tabu!)]"
                        priority = 4
                else:
                    if obj_type in ["broadband", "cluster"]:
                        rec_tag = "[🟢 DWARF 3: Astro Filter]"
                    elif obj_type == "narrowband":
                        rec_tag = "[🟢 DWARF 3: Duo-Band Filter]"
                    else:
                        rec_tag = "[🟢 DWARF 3: Duo-Band oder Astro]"
                    priority = 1
                
                matched.append({
                    "cat": t['cat'],
                    "name": t['name'],
                    "max_alt": max_alt,
                    "transit": transit_time,
                    "rec_tag": rec_tag,
                    "priority": priority
                })
                
    if moon_illumination >= 50:
        matched.sort(key=lambda x: (x['priority'], -x['max_alt']))
    else:
        matched.sort(key=lambda x: -x['max_alt'])
        
    top_targets = matched[:15]
    formatted = [f"• {t['cat']} ({t['name']}) {t['rec_tag']} - Max: {t['max_alt']}° (Zenit: {t['transit']} Uhr)" for t in top_targets]
    return formatted if formatted else ["• Keine Objekte gelistet"]

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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("Lade Wetter- & Astrodaten...")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            raw_response = response.read().decode('utf-8')
            if not raw_response or not raw_response.strip().startswith('{'):
                print("Fehler: API hat kein gültiges JSON geliefert.", file=sys.stderr)
                return
            data = json.loads(raw_response)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"API Fehler: {error_body}", file=sys.stderr)
        raise e
    except Exception as e:
        print(f"Netzwerk- oder Parsing-Fehler: {e}", file=sys.stderr)
        return

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

    vevents = []

    for day in range(7):
        start_idx = day * 24
        end_idx = start_idx + 24
        
        night_indices = [k for k in range(start_idx, end_idx) if k < len(is_day_hourly) and is_day_hourly[k] == 0]
        if not night_indices:
            night_indices = [k for k in range(start_idx, end_idx) if k < len(times_hourly)]
            
        n_clouds = [clouds_hourly for k in night_indices if k < len(clouds_hourly)]
        n_low = [clouds_low for k in night_indices if k < len(clouds_low)] if clouds_low else n_clouds
        n_mid = [clouds_mid for k in night_indices if k < len(clouds_mid)] if clouds_mid else n_clouds
        n_high = [clouds_high for k in night_indices if k < len(clouds_high)] if clouds_high else n_clouds
        
        n_humidity = [humidity_hourly for k in night_indices if k < len(humidity_hourly)]
        n_precip_prob = [precip_prob_hourly for k in night_indices if k < len(precip_prob_hourly)]
        n_precip = [precip_hourly for k in night_indices if k < len(precip_hourly)]
        
        avg_cloud = sum(n_clouds) / len(n_clouds) if n_clouds else 50
        avg_low = sum(n_low) / len(n_low) if n_low else avg_cloud
        avg_mid = sum(n_mid) / len(n_mid) if n_mid else avg_cloud
        avg_high = sum(n_high) / len(n_high) if n_high else avg_cloud
        
        avg_humidity = sum(n_humidity) / len(n_humidity) if n_humidity else 50
        max_precip_prob = max(n_precip_prob) if n_precip_prob else 0
        total_precip = sum(n_precip) if n_precip else 0.0
        
        moon_phase_val = moon_phases[day] if day < len(moon_phases) else 0.5
        moon_illumination = int((1 - abs(moon_phase_val - 0.5) * 2) * 100)
        m_rise = format_time_str(moonrises[day] if day < len(moonrises) else "")
        m_set = format_time_str(moonsets[day] if day < len(moonsets) else "")
        
        weighted_cloud = (avg_low * 0.5) + (avg_mid * 0.3) + (avg_high * 0.2)
        cloud_score = (100 - weighted_cloud) * 0.75
        
        if weighted_cloud < 35:
            effective_moon_illumination = moon_illumination * 0.15
        else:
            effective_moon_illumination = moon_illumination
            
        moon_score = (100 - effective_moon_illumination) * 0.15
        humidity_score = (100 - max(0, avg_humidity - 70) * 3.33) * 0.10
        precip_penalty = (max_precip_prob / 100.0) * 30
        
        total_score = max(0, min(100, int(cloud_score + moon_score + humidity_score - precip_penalty)))
        
        if total_score <= 60:
            continue
            
        status_icon = "🟢" if total_score > 80 else "🟡"
            
        date_str = times_hourly[start_idx][:10]
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        summary = f"🔭 {status_icon} Deep Sky: {total_score}%"
        
        dusk_utc, dawn_utc = calculate_astronomical_night(date_str)
        sunset_raw = sunsets[day] if day < len(sunsets) else ""
        sunrise_raw = sunrises[day+1] if (day+1) < len(sunrises) else (sunrises[day] if day < len(sunrises) else "")
        sunset_time = format_time_str(sunset_raw)
        sunrise_time = format_time_str(sunrise_raw)
        
        if dusk_utc and dawn_utc:
            astro_str = f"{dusk_utc.strftime('%H:%M')} - {dawn_utc.strftime('%H:%M')} UTC"
        else:
            astro_str = f"Sommernacht (Sonnenuntergang: {sunset_time} - {sunrise_time})"

        targets = get_sorted_targets(date_str, dt_obj.month, moon_illumination)
        targets_str = "\n".join(targets)
        
        dew_warning = " ⚠️ (Tau-Risiko)" if avg_humidity >= 85 else ""
        precip_str = f"{max_precip_prob}% ({total_precip:.1f} mm)" if max_precip_prob > 0 else "0% (Trocken)"
        
        raw_description = (
            f"Astro-Dunkelheit (Sonne <= -18°): {astro_str}\n"
            f"Bewölkung (Nacht): Tiefe {int(avg_low)}% | Mid {int(avg_mid)}% | High {int(avg_high)}% (Schnitt: {int(avg_cloud)}%)\n"
            f"Mond: ~{moon_illumination}% | Aufgang: {m_rise} | Untergang: {m_set}\n"
            f"Niederschlag: {precip_str}\n"
            f"Luftfeuchtigkeit: {int(avg_humidity)}%{dew_warning}\n\n"
            f"DWARF 3 Empfehlungen & Filter (nach Zenit):\n"
            f"{targets_str}\n\n"
            f"Erstellt via Open-Meteo Astro API"
        )
        
        vevent_str = ics_builder.create_vevent(
            uid=f"astro-{date_str}@deepsky",
            dt_start_utc=dusk_utc,
            dt_end_utc=dawn_utc,
            summary=summary,
            description_text=raw_description,
            alarm_hours_before=6
        )
        vevents.append(vevent_str)

    vcal_str = ics_builder.build_calendar_ics(vevents)
    ics_builder.save_ics("deepsky.ics", vcal_str)

if __name__ == "__main__":
    generate_ics()
