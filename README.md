# Calendar Events Display

This project automatically fetches and displays the next 5 upcoming events from a Google Calendar ICS feed, updating daily via GitHub Actions.

## Setup Instructions

### 1. Repository Setup

1. Create a new GitHub repository
2. Clone the repository to your local machine
3. Copy these files into your repository:
   - `fetch_calendar.py` - Python script to fetch calendar events
   - `styles.css` - Stylesheet for the webpage
   - `requirements.txt` - Python dependencies
   - `.github/workflows/update-calendar.yml` - GitHub Actions workflow

### 2. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under "Source", select **Deploy from a branch**
4. Select the **main** branch and **/root** folder
5. Click **Save**

### 3. Run the Workflow

The workflow will run automatically daily at 6:00 AM UTC. You can also trigger it manually:

1. Go to the **Actions** tab in your repository
2. Click on "Update Calendar Events" workflow
3. Click **Run workflow**

### 4. View Your Calendar Page

After the first workflow run completes:
- Your calendar page will be available at: `https://[your-username].github.io/[repository-name]/`

## How It Works

1. **Python Script** (`fetch_calendar.py`):
   - Fetches the ICS calendar feed
   - Parses upcoming events
   - Generates an HTML page with the next 5 events

2. **GitHub Actions** (`.github/workflows/update-calendar.yml`):
   - Runs daily at 6:00 AM UTC
   - Executes the Python script
   - Commits and pushes the updated HTML file

3. **GitHub Pages**:
   - Automatically deploys the updated HTML file
   - Makes your calendar accessible via a public URL

## Customization

### Change Update Frequency

Edit the cron schedule in `.github/workflows/update-calendar.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Currently runs at 6:00 AM UTC daily
```

Examples:
- Every 6 hours: `'0 */6 * * *'`
- Twice daily (6 AM and 6 PM): `'0 6,18 * * *'`
- Every hour: `'0 * * * *'`

### Change Number of Events

Edit the `count` parameter in `fetch_calendar.py`:

```python
events = get_upcoming_events(cal, count=5)  # Change 5 to any number
```

### Change Calendar Source

Edit the `ICS_URL` in `fetch_calendar.py`:

```python
ICS_URL = "YOUR_CALENDAR_ICS_URL_HERE"
```

## Files Included

- `fetch_calendar.py` - Main Python script
- `styles.css` - Webpage styling
- `requirements.txt` - Python dependencies
- `.github/workflows/update-calendar.yml` - Automation workflow
- `README.md` - This file

## Troubleshooting

**Workflow fails:**
- Check the Actions tab for error messages
- Ensure GitHub Actions is enabled for your repository
- Verify the calendar URL is accessible

**Page not updating:**
- Check if the workflow is running (Actions tab)
- Verify GitHub Pages is enabled and pointing to the correct branch
- Allow a few minutes for GitHub Pages to update after commits

**No events showing:**
- Verify the calendar has upcoming events
- Check the ICS URL is correct and publicly accessible
- Review workflow logs for parsing errors
