import sys
from datetime import datetime, timezone

def fold_line(text, limit=75):
    """ Striktes RFC 5545 Line-Folding (max 75 Bytes pro Zeile) """
    encoded = text.encode('utf-8')
    if len(encoded) <= limit:
        return text
    lines = []
    while len(encoded) > limit:
        split_at = limit
        while split_at > 0 and (encoded[split_at] & 0xC0) == 0x80:
            split_at -= 1
        lines.append(encoded[:split_at].decode('utf-8'))
        encoded = b' ' + encoded[split_at:]
    if encoded:
        lines.append(encoded.decode('utf-8'))
    return "\r\n ".join(lines)

def escape_text(text):
    """ Escaping von Sonderzeichen nach iCalendar Standard """
    return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

def create_vevent(uid, dt_start_utc, dt_end_utc, summary, description_text, alarm_hours_before=6):
    """ Erstellt einen RFC 5545-konformen VEVENT-Eintrag für Apple iCloud """
    if dt_start_utc and dt_end_utc:
        # Garantiert Apple-Kompatibilität: DTEND muss nach DTSTART liegen
        if dt_end_utc <= dt_start_utc:
            raise ValueError(f"Sicherheitsblockade: DTEND ({dt_end_utc}) liegt nicht nach DTSTART ({dt_start_utc})!")
        
        dt_start_str = dt_start_utc.strftime('%Y%m%dT%H%M%SZ')
        dt_end_str = dt_end_utc.strftime('%Y%m%dT%H%M%SZ')
        dt_lines = [f"DTSTART:{dt_start_str}", f"DTEND:{dt_end_str}"]
    else:
        date_str = uid.split('-')[1] if '-' in uid else datetime.now(timezone.utc).strftime('%Y%m%d')
        dt_lines = [f"DTSTART;VALUE=DATE:{date_str.replace('-', '')}"]

    escaped_desc = escape_text(description_text)

    vevent = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    ]
    vevent.extend(dt_lines)
    vevent.append(fold_line(f"SUMMARY:{summary}"))
    vevent.append(fold_line(f"DESCRIPTION:{escaped_desc}"))

    if alarm_hours_before:
        vevent.extend([
            "BEGIN:VALARM",
            f"TRIGGER:-PT{alarm_hours_before}H",
            "ACTION:DISPLAY",
            fold_line("DESCRIPTION:🔭 Deep Sky Fotografie: Gute Bedingungen heute Nacht!"),
            "END:VALARM"
        ])

    vevent.append("END:VEVENT")
    return "\r\n".join(vevent)

def build_calendar_ics(vevents, calendar_name="Deep Sky Vorhersage"):
    """ Baut das vollständige VCALENDAR Dokument mit CRLF-Zeilenendungen """
    vcal = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//DeepSkyForecast//DE",
        f"X-WR-CALNAME:{calendar_name}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H"
    ]
    if vevents:
        vcal_str = "\r\n".join(vcal) + "\r\n" + "\r\n".join(vevents) + "\r\nEND:VCALENDAR\r\n"
    else:
        vcal_str = "\r\n".join(vcal) + "\r\nEND:VCALENDAR\r\n"
    return vcal_str

def save_ics(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Datei erfolgreich als '{filepath}' gespeichert.")
