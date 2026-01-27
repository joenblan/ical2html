#!/usr/bin/env python3
"""
Fetch upcoming events from a Google Calendar ICS feed and generate an HTML page.
"""

import requests
from icalendar import Calendar
from datetime import datetime, timezone
import pytz

def fetch_and_parse_calendar(ics_url):
    """Fetch ICS file and parse calendar events."""
    response = requests.get(ics_url)
    response.raise_for_status()
    
    cal = Calendar.from_ical(response.content)
    return cal

def get_upcoming_events(cal, count=5):
    """Extract upcoming events from calendar."""
    now = datetime.now(timezone.utc)
    events = []
    
    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart')
            summary = component.get('summary')
            
            if dtstart and summary:
                # Handle both datetime and date objects
                if hasattr(dtstart.dt, 'tzinfo'):
                    event_time = dtstart.dt
                    if event_time.tzinfo is None:
                        event_time = event_time.replace(tzinfo=timezone.utc)
                else:
                    # If it's a date object, convert to datetime at midnight UTC
                    event_time = datetime.combine(dtstart.dt, datetime.min.time()).replace(tzinfo=timezone.utc)
                
                # Only include future events
                if event_time >= now:
                    events.append({
                        'datetime': event_time,
                        'summary': str(summary)
                    })
    
    # Sort by date and return the next N events
    events.sort(key=lambda x: x['datetime'])
    return events[:count]

def format_event_html(event):
    """Format a single event as HTML list items."""
    dt = event['datetime']
    
    # Convert to Brussels timezone
    brussels_tz = pytz.timezone('Europe/Brussels')
    dt_brussels = dt.astimezone(brussels_tz)
    
    # Dutch day and month names
    days_nl = ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag']
    months_nl = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni', 
                 'juli', 'augustus', 'september', 'oktober', 'november', 'december']
    
    # Format date in Dutch (e.g., "maandag 27 januari 2026")
    day_name = days_nl[dt_brussels.weekday()]
    date_str = f"{day_name} {dt_brussels.day} {months_nl[dt_brussels.month]} {dt_brussels.year}"
    
    # Check if this is an all-day event (original time was midnight UTC)
    if dt.hour == 0 and dt.minute == 0:
        time_str = "hele dag"
    else:
        # Format time in 24-hour format (e.g., "14:30")
        time_str = dt_brussels.strftime('%H:%M')
    
    return f"""    <li>
      <strong>{event['summary']}</strong><br>
      {date_str} - {time_str}
    </li>"""

def generate_html(events):
    """Generate complete HTML page with events."""
    
    events_html = '\n'.join([format_event_html(event) for event in events])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Upcoming Calendar Events</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <h1>Upcoming Events</h1>
  <h2>Next 5 Events</h2>
  <ul>
{events_html}
  </ul>
  <p style="margin-top: 2vh; font-size: 0.9em; color: #888;">
    Last updated: {datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p UTC')}
  </p>
</body>
</html>"""
    
    return html

def main():
    """Main function to fetch calendar and generate HTML."""
    ICS_URL = "https://calendar.google.com/calendar/ical/mellegbs%40gmail.com/public/basic.ics"
    
    print("Fetching calendar...")
    cal = fetch_and_parse_calendar(ICS_URL)
    
    print("Extracting upcoming events...")
    events = get_upcoming_events(cal, count=5)
    
    if not events:
        print("No upcoming events found.")
        events = []
    else:
        print(f"Found {len(events)} upcoming events")
    
    print("Generating HTML...")
    html = generate_html(events)
    
    # Write HTML file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("HTML file generated successfully: index.html")

if __name__ == "__main__":
    main()
