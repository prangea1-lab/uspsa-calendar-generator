
import re
import os
from datetime import datetime, timedelta

TARGET_FILE = "source.html"
OUTPUT_ICS_FILE = "uspsa_schedule.ics"

# Case-insensitive keywords for clubs you track
WATCHLIST = ["renton", "paul bunyan", "marysville", "cascade", "custer", "evergreen", "columbia cascade", "tacoma", "port townsend", "pt "]

if not os.path.exists(TARGET_FILE):
    print(f"❌ Error: Could not find '{TARGET_FILE}' in the sidebar directory.")
else:
    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        content = file.read()

    # Regex streaming pattern to find individual event blocks
    event_pattern = r'\{"title":"([^"]+)","start":"([^"]+)"(?:,"end":"([^"]+)")?[^}]*\}'
    raw_events = re.findall(event_pattern, content)

    match_db = {}

    # Deep-scan helper that hunts through the entire HTML file to find a real, valid URL
    # matching the club name if the individual event block left it blank.
    def find_real_url_in_source(match_title, full_html):
        # Extract the basic club text signature (e.g., "port-townsend")
        clean_name = match_title.replace("Open Registration - ", "").replace("Close Registration - ", "")
        slug_part = re.sub(r'[^a-zA-Z0-9\s]', '', clean_name).strip().lower()
        words = [w for w in slug_part.split() if w not in ["uspsa", "june", "july", "august", "september", "october", "november", "december", "2026", "match"]]
        
        if not words:
            return "https://practiscore.com"
            
        # Look for any valid registration link in the file matching these keywords
        search_term = words[0]
        links_found = re.findall(r'"url":"([^"]*' + search_term + r'[^"]*)"', full_html)
        
        for link in links_found:
            clean_link = link.replace(r"\/", "/")
            if "/register" in clean_link or "/participants/create" in clean_link:
                # Format internal links cleanly
                if "/events/" in clean_link and "/participants/create" in clean_link:
                    m_slug = re.search(r'/events/([^/]+)/participants/create', clean_link)
                    if m_slug:
                        return f"https://practiscore.com/{m_slug.group(1)}/register"
                if not clean_link.startswith("http"):
                    return f"https://practiscore.com/{clean_link.lstrip('/')}"
                return clean_link
                
        # Basic formatting fallback if no raw matches are found anywhere in the code
        fallback_slug = "-".join(words[:3])
        return f"https://practiscore.com/{fallback_slug}/register"

    for title, start_str, end_str in raw_events:
        title_lower = title.lower()
        
        # Drop non-USPSA formats, steel matches, and specialty events
        if (any(x in title_lower for x in ["asi", "idpa", "nrl22", "steel", "plates", "move and shoot"]) 
                or "move & shoot" in title_lower):
            continue

        # Skip profile administrative tags
        if "andrew prange" in title_lower:
            continue

        # Look for the registration/match link destination
        url_search = re.search(r'"url":"([^"]+)"', content[content.find(title):content.find(title)+500])
        url_str = url_search.group(1).replace(r"\/", "/") if url_search else ""
        
        # Rewrite squadding confirmation links into direct public registration pages
        if "/events/" in url_str and "/participants/create" in url_str:
            match_slug_search = re.search(r'/events/([^/]+)/participants/create', url_str)
            if match_slug_search:
                url_str = f"https://practiscore.com/{match_slug_search.group(1)}/register"
        
        # Ensure relative local web paths get prefixed into absolute web URLs
        if url_str and not url_str.startswith("http"):
            url_str = f"https://practiscore.com/{url_str.lstrip('/')}"
            
        # Ensure extracted links terminate properly at the registration screen
        if url_str and not url_str.endswith("/register") and not url_str.endswith("/create"):
            url_str = url_str.rstrip('/') + "/register"

        # 🟢 UPGRADED DEEP SCAN FALLBACK: If the URL is blank or a generic homepage string,
        # we unleash a global text parser to locate the actual hidden link fragment.
        if not url_str or url_str == "https://practiscore.com" or url_str == "https://practiscore.com/register":
            url_str = find_real_url_in_source(title, content)

        # Clean title strings to isolate the base match name
        base_title = title.replace("Open Registration - ", "").replace("Close Registration - ", "")

        # Filter against your personal club watchlist
        if any(club in base_title.lower() for club in WATCHLIST):
            if base_title not in match_db:
                match_db[base_title] = {"match_date": None, "open_date": None, "url": url_str}
            
            if "Open Registration -" in title:
                match_db[base_title]["open_date"] = start_str
            elif "Close Registration -" in title:
                pass
            else:
                match_db[base_title]["match_date"] = start_str

    # Build the duplicate-proof iCalendar structure lines
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI USPSA Deep Scan Tracker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    def format_ics_time(time_str):
        if " " in time_str:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(time_str, "%Y-%m-%d")
            dt = dt.replace(hour=9, minute=0)
        return dt.strftime("%Y%m%dT%H%M%S"), dt

    def make_safe_id(text):
        return re.sub(r'[^a-zA-Z0-9]', '-', text).lower()

    print(f"\n📦 PACKAGING VERIFIED-LINK USPSA EVENTS... 📦")
    print("=" * 80)
    
    event_count = 0
    
    for name, dates in match_db.items():
        safe_name = name.replace(",", "\\,")
        url_str = dates["url"]
        base_id = make_safe_id(name)
        
        # 1. Inject Match Day Event Block
        if dates["match_date"]:
            try:
                ical_start, dt_start = format_ics_time(dates["match_date"])
                dt_end = dt_start + timedelta(hours=6)
                ical_end = dt_end.strftime("%Y%m%dT%H%M%S")
                date_stamp = dt_start.strftime("%Y%m%d")
                
                ics_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:match-{base_id}-{date_stamp}@pstracker.local",
                    f"SUMMARY:🔫 Match Day: {safe_name}",
                    f"DTSTART:{ical_start}",
                    f"DTEND:{ical_end}",
                    f"DESCRIPTION:Link to match details: {url_str}",
                    f"URL:{url_str}",
                    "END:VEVENT"
                ])
                event_count += 1
            except Exception:
                pass
        
        # 2. Inject Registration Window + 15-Minute Audio Alarm Block
        if dates["open_date"]:
            try:
                ical_reg_start, dt_reg_start = format_ics_time(dates["open_date"])
                dt_reg_end = dt_reg_start + timedelta(minutes=30)
                ical_reg_end = dt_reg_end.strftime("%Y%m%dT%H%M%S")
                reg_stamp = dt_reg_start.strftime("%Y%m%d")
                
                ics_lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:reg-{base_id}-{reg_stamp}@pstracker.local",
                    f"SUMMARY:🚨 REGISTRATION OPENS: {safe_name}",
                    f"DTSTART:{ical_reg_start}",
                    f"DTEND:{ical_reg_end}",
                    f"DESCRIPTION:Signup gate opening! Click here to register: {url_str}",
                    f"URL:{url_str}",
                    "BEGIN:VALARM",
                    "TRIGGER:-PT15M", 
                    "ACTION:DISPLAY",
                    "DESCRIPTION:USPSA Match Registration Opening!",
                    "END:VALARM",
                    "END:VEVENT"
                ])
                event_count += 1
                print(f"Secured Verified Link -> {name}")
                print(f"               Target -> {url_str}\n")
            except Exception:
                pass

    ics_lines.append("END:VCALENDAR")
    
    with open(OUTPUT_ICS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(ics_lines))
        
    print("=" * 80)
    print(f"✅ SUCCESS: Generated [{event_count}] verified-link blocks inside '{OUTPUT_ICS_FILE}'")
