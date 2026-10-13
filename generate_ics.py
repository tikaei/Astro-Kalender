import json
import math
import ssl
import sys
import urllib.request
from datetime import UTC, datetime, timedelta

import ics_builder
from dso_catalog import DSO_CATALOG

# --- KOORDINATEN (Neukirchen OT Adorf) ---
LATITUDE = 50.7725
LONGITUDE = 12.8860


def calculate_astronomical_night(date_str, lat=LATITUDE, lon=LONGITUDE):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday
        gamma = (2 * math.pi / 365) * (day_of_year - 1)
        eqtime = 229.18 * (
            0.000075
            + 0.001868 * math.cos(gamma)
            - 0.032077 * math.sin(gamma)
            - 0.014615 * math.cos(2 * gamma)
            - 0.040849 * math.sin(2 * gamma)
        )
        decl = (
            0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.00148 * math.sin(3 * gamma)
        )

        lat_rad = math.radians(lat)
        zenith = math.radians(108.0)  # -18° Elevation

        cos_ha = (math.cos(zenith) - math.sin(lat_rad) * math.sin(decl)) / (
            math.cos(lat_rad) * math.cos(decl)
        )
        if cos_ha > 1.0 or cos_ha < -1.0:
            return None, None

        ha_deg = math.degrees(math.acos(cos_ha))
        ha_minutes = ha_deg * 4.0

        solar_noon_utc = 720 - (4 * lon) - eqtime
        dusk_utc_min = solar_noon_utc + ha_minutes
        dawn_utc_min = solar_noon_utc - ha_minutes

        dusk_utc = datetime(dt.year, dt.month, dt.day, tzinfo=UTC) + timedelta(minutes=dusk_utc_min)
        dawn_utc = datetime(dt.year, dt.month, dt.day, tzinfo=UTC) + timedelta(
            days=1, minutes=dawn_utc_min
        )
        return dusk_utc, dawn_utc
    except Exception:  # noqa: BLE001
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

    transit_dt_utc = datetime(dt.year, dt.month, dt.day, tzinfo=UTC) + timedelta(
        hours=transit_utc_hours
    )

    m_last_sun = 31 - (datetime(dt.year, 3, 31).weekday() + 1) % 7
    o_last_sun = 31 - (datetime(dt.year, 10, 31).weekday() + 1) % 7
    dst_start = datetime(dt.year, 3, m_last_sun, 2, 0, tzinfo=UTC)
    dst_end = datetime(dt.year, 10, o_last_sun, 3, 0, tzinfo=UTC)

    is_dst = dst_start <= transit_dt_utc < dst_end
    local_offset = timedelta(hours=2 if is_dst else 1)

    transit_dt_local = transit_dt_utc + local_offset
    return transit_dt_local.strftime("%H:%M")


def get_sorted_targets(date_str, month, moon_illumination):
    matched = []
    for t in DSO_CATALOG:
        if month in t["months"]:
            max_alt = round(90.0 - abs(LATITUDE - t["dec"]))
            if max_alt > 10:
                transit_time = calculate_transit_time_str(date_str, t["ra"])
                obj_type = t.get("type", "broadband")

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
                    else:  # broadband
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
                    "cat": t["cat"],
                    "name": t["name"],
                    "max_alt": max_alt,
                    "transit": transit_time,
                    "rec_tag": rec_tag,
                    "priority": priority,
                })

    if moon_illumination >= 50:
        matched.sort(key=lambda x: (x["priority"], -x["max_alt"]))
    else:
        matched.sort(key=lambda x: -x["max_alt"])

    top_targets = matched[:15]
    formatted = [
        f"• {t['cat']} ({t['name']}) {t['rec_tag']} - Max: {t['max_alt']}° (Zenit: {t['transit']} Uhr)"
        for t in top_targets
    ]
    return formatted if formatted else ["• Keine Objekte gelistet"]


def format_time_str(iso_val):
    if isinstance(iso_val, list):
        iso_val = iso_val[0] if iso_val else ""
    iso_str = str(iso_val) if iso_val else ""
    if not iso_str or iso_str == "N/A" or len(iso_str) < 16:
        return "N/A"
    return iso_str[-5:]


def safe_float(val, default=None):
    if isinstance(val, list):
        val = val[0] if val else None
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def parse_time_str(val):
    if isinstance(val, list):
        val = val[0] if val else ""
    return str(val) if val else ""


def extract_numbers(data_list, indices, default=None):
    result = []
    if not isinstance(data_list, list):
        return result
    for k in indices:
        if 0 <= k < len(data_list):
            val = safe_float(data_list[k], default)
            if val is not None:
                result.append(val)
    return result


def generate_ics():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,"
        f"relative_humidity_2m,precipitation_probability,precipitation&"
        f"daily=sunset,sunrise,moonrise,moonset,moon_phase&"
        f"forecast_days=7&timezone=Europe/Berlin"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("Lade Wetterdaten von Open-Meteo...", flush=True)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            raw_response = response.read().decode("utf-8")
            if not raw_response or not raw_response.strip().startswith("{"):
                print("Fehler: API hat kein gültiges JSON geliefert.", file=sys.stderr, flush=True)
                return
            data = json.loads(raw_response)
    except Exception as e:  # noqa: BLE001
        print(f"Netzwerk- oder Parsing-Fehler: {e}", file=sys.stderr, flush=True)
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
    times_hourly = hourly.get("time", [])

    sunsets = daily.get("sunset", [])
    sunrises = daily.get("sunrise", [])
    moonrises = daily.get("moonrise", [])
    moonsets = daily.get("moonset", [])
    moon_phases = daily.get("moon_phase", [])

    vevents = []
    print("=== VORHERSAGE FÜR DIE NÄCHSTEN 7 TAGE ===", flush=True)

    daily_times = daily.get("time", [])

    for day in range(7):
        if day < len(daily_times):
            date_str = parse_time_str(daily_times[day])[:10]
        elif (day * 24) < len(times_hourly):
            date_str = parse_time_str(times_hourly[day * 24])[:10]
        else:
            dt_fallback = datetime.now() + timedelta(days=day)
            date_str = dt_fallback.strftime("%Y-%m-%d")

        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        next_date_str = (dt_obj + timedelta(days=1)).strftime("%Y-%m-%d")

        night_indices = []
        for k, t_raw in enumerate(times_hourly):
            t_str = parse_time_str(t_raw)
            if len(t_str) >= 13:
                d_part = t_str[:10]
                try:
                    h_part = int(t_str[11:13])
                except ValueError:
                    continue

                if (d_part == date_str and h_part >= 19) or (d_part == next_date_str and h_part <= 5):
                    night_indices.append(k)

        if not night_indices:
            start_k = day * 24
            night_indices = list(range(start_k, min(start_k + 24, len(times_hourly))))

        n_clouds = extract_numbers(clouds_hourly, night_indices)
        n_low = extract_numbers(clouds_low, night_indices)
        n_mid = extract_numbers(clouds_mid, night_indices)
        n_high = extract_numbers(clouds_high, night_indices)
        n_humidity = extract_numbers(humidity_hourly, night_indices)
        n_precip_prob = extract_numbers(precip_prob_hourly, night_indices)
        n_precip = extract_numbers(precip_hourly, night_indices)

        avg_cloud = sum(n_clouds) / len(n_clouds) if n_clouds else 50.0
        avg_low = sum(n_low) / len(n_low) if n_low else avg_cloud
        avg_mid = sum(n_mid) / len(n_mid) if n_mid else avg_cloud
        avg_high = sum(n_high) / len(n_high) if n_high else avg_cloud

        max_cloud = max(n_clouds) if n_clouds else avg_cloud
        max_low = max(n_low) if n_low else avg_low
        max_mid = max(n_mid) if n_mid else avg_mid

        weighted_avg_cloud = (avg_low * 0.4) + (avg_mid * 0.3) + (avg_high * 0.2) + (avg_cloud * 0.1)
        weighted_max_cloud = (max_low * 0.5) + (max_mid * 0.3) + (max_cloud * 0.2)

        effective_cloud = (weighted_avg_cloud * 0.6) + (weighted_max_cloud * 0.4)
        cloud_score = (100 - effective_cloud) * 0.75

        avg_humidity = sum(n_humidity) / len(n_humidity) if n_humidity else 50.0
        max_precip_prob = max(n_precip_prob) if n_precip_prob else 0.0
        total_precip = sum(n_precip) if n_precip else 0.0

        moon_phase_raw = moon_phases[day] if day < len(moon_phases) else 0.5
        moon_phase_val = safe_float(moon_phase_raw, default=0.5)
        moon_illumination = int((1 - abs(moon_phase_val - 0.5) * 2) * 100)

        m_rise = format_time_str(moonrises[day] if day < len(moonrises) else "")
        m_set = format_time_str(moonsets[day] if day < len(moonsets) else "")

        if effective_cloud < 15:
            effective_moon_illumination = moon_illumination * 0.20
        else:
            effective_moon_illumination = moon_illumination

        moon_score = (100 - effective_moon_illumination) * 0.15
        humidity_score = (100 - max(0, avg_humidity - 70) * 3.33) * 0.10
        precip_penalty = (max_precip_prob / 100.0) * 30

        total_score = max(0, min(100, int(cloud_score + moon_score + humidity_score - precip_penalty)))

        if total_score <= 60:
            print(
                f"[GEFILTERT] {date_str}: Score {total_score}% | Schnitt Wolken: {int(avg_cloud)}%, Spitze: {int(max_cloud)}%, Feuchte: {int(avg_humidity)}%",
                flush=True,
            )
            continue

        status_symbol = "GRUEN" if total_score > 80 else "GELB"
        print(
            f"[{status_symbol}] {date_str}: Score {total_score}% | Schnitt Wolken: {int(avg_cloud)}%, Spitze: {int(max_cloud)}%, Feuchte: {int(avg_humidity)}%",
            flush=True,
        )

        status_icon = "🟢" if total_score > 80 else "🟡"
        summary = f"🔭 {status_icon} Deep Sky: {total_score}%"

        dusk_utc, dawn_utc = calculate_astronomical_night(date_str)
        sunset_raw = sunsets[day] if day < len(sunsets) else ""
        sunrise_raw = (
            sunrises[day + 1]
            if (day + 1) < len(sunrises)
            else (sunrises[day] if day < len(sunrises) else "")
        )
        sunset_time = format_time_str(sunset_raw)
        sunrise_time = format_time_str(sunrise_raw)

        if dusk_utc and dawn_utc:
            astro_str = f"{dusk_utc.strftime('%H:%M')} - {dawn_utc.strftime('%H:%M')} UTC"
        else:
            astro_str = f"Sommernacht (Sonnenuntergang: {sunset_time} - {sunrise_time})"

        targets = get_sorted_targets(date_str, dt_obj.month, moon_illumination)
        targets_str = "\n".join(targets)

        dew_warning = " ⚠️ (Tau-Risiko)" if avg_humidity >= 85 else ""
        precip_str = f"{int(max_precip_prob)}% ({total_precip:.1f} mm)" if max_precip_prob > 0 else "0% (Trocken)"

        raw_description = (
            f"Astro-Dunkelheit (Sonne <= -18°): {astro_str}\n"
            f"Bewölkung (Nacht): Schnitt {int(avg_cloud)}% | Spitze {int(max_cloud)}% (Low {int(avg_low)}% / High {int(avg_high)}%)\n"
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
            alarm_hours_before=6,
        )
        vevents.append(vevent_str)

    print("===========================================", flush=True)
    vcal_str = ics_builder.build_calendar_ics(vevents)
    ics_builder.save_ics("deepsky.ics", vcal_str)


if __name__ == "__main__":
    generate_ics()
