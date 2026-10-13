from datetime import UTC, datetime


def create_vevent(uid, dt_start_utc, dt_end_utc, summary, description_text, alarm_hours_before=6):
    now_utc = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    if dt_start_utc and dt_end_utc:
        dtstart = dt_start_utc.strftime("%Y%m%dT%H%M%SZ")
        dtend = dt_end_utc.strftime("%Y%m%dT%H%M%SZ")
    else:
        dtstart = now_utc
        dtend = now_utc

    description_formatted = description_text.replace("\n", "\\n")

    alarm_block = ""
    if alarm_hours_before:
        alarm_block = (
            "BEGIN:VALARM\r\n"
            "ACTION:DISPLAY\r\n"
            "DESCRIPTION:Astro-Wetter Erinnerung\r\n"
            f"TRIGGER:-PT{alarm_hours_before}H\r\n"
            "END:VALARM\r\n"
        )

    vevent = (
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now_utc}\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description_formatted}\r\n"
        f"{alarm_block}"
        "END:VEVENT\r\n"
    )
    return vevent


def build_calendar_ics(vevents_list):
    events_str = "".join(vevents_list)
    vcal = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Astro-Kalender Adorf//DWARF 3//DE\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "X-WR-CALNAME:Astro-Wetter & DWARF 3\r\n"
        "X-WR-TIMEZONE:Europe/Berlin\r\n"
        f"{events_str}"
        "END:VCALENDAR\r\n"
    )
    return vcal


def save_ics(filename, content):
    with open(filename, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)
    print(f"Datei erfolgreich als '{filename}' gespeichert.", flush=True)
