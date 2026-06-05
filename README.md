# uspsa-calendar-generator
Generates an ICS file from PS Calendar view page with registration links and reminders

# USPSA Practiscore Calendar Generator 🔫

This script converts a saved Practiscore Calendar webpage into a duplicate-proof `.ics` file packed with match dates, registration opening times, direct signup links, and 15-minute audio alarms. 

## How to Use It (The 60-Second Routine)

1. **Save the Page:** * Go to your Practiscore Calendar view for the month you want to track.
   * **Right-click** anywhere on the empty space of the page and select **Save As...** (or **Save Page As...**).
   * Ensure the format dropdown is set to **Webpage, HTML Only** (not Webpage, Complete), name the file `source.html`, and save it to your computer.

2. **Run the Script:** * Open this project's Google Colab notebook (or your local Python environment).
   * Drag and drop your saved `source.html` file into the file tray panel on the left sidebar.
   * Run the script cell.

3. **Import to Your Calendar:** * Click the refresh icon on the Colab file tray, then download the newly generated **`uspsa_schedule.ics`** file.
   * Open Google Calendar, Apple Calendar, or Outlook on your desktop browser.
   * Go to **Settings -> Import & Export**, upload the file, and choose your preferred calendar layer!

*Note: This script automatically filters out ASI, IDPA, NRL22, and casual local steel matches/plates to keep your schedule 100% focused on core USPSA & PCSL events.*
