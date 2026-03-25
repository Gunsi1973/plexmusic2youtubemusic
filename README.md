# Plex to YouTube Music Sync

This project contains two Python scripts to manage and synchronize your local Plex music library with YouTube Music.

* `sync_tool.py`: Synchronizes selected Plex audio playlists to YouTube Music. Matches tracks based on artist, title, and track duration.
* `cleanup_duplicates.py`: Scans your YouTube Music playlists and safely removes duplicate tracks.

## Prerequisites
* Python 3.8 or higher
* A local Plex Media Server with a music library
* A YouTube Music account

## Installation

1. Clone this repository or download the files.
2. Open your terminal and navigate to the project folder.
3. Create and activate a virtual environment:

For Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

For macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

4. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Plex Setup (.env)
Create a file named `.env` in the root folder of your project and add your Plex details:
```text
PLEX_URL=http://YOUR_PLEX_IP:32400
PLEX_TOKEN=your_plex_token_here
```

**How to find your Plex Token:**
* Sign in to the Plex Web App in your browser.
* Navigate to your music library and select any track or album.
* Click the three dots (More) and select "Get Info".
* Click "View XML" at the bottom of the window.
* A new browser tab will open. Look at the URL bar. Copy the string of characters exactly after `&X-Plex-Token=`.

### 2. YouTube Music Authentication (browser.json)
The script uses the `ytmusicapi` library, which requires your browser's session headers to authenticate.

1. Open your browser and go to music.youtube.com. Ensure you are logged in.
2. Open the Developer Tools (Press F12 or Ctrl+Shift+I) and go to the "Network" tab.
3. Perform an action on the page (like clicking "Home") to generate network traffic.
4. Search for a request named "browse" or starting with "v1".
5. Click on that request, scroll to the "Request Headers" section, and copy the entire raw text block (starting from POST /api/... down to the end of the cookie: string).
6. Open your terminal (ensure your .venv is active) and run:
```bash
ytmusicapi browser
```

7. Paste the headers into your terminal:
* Right-click to paste your copied headers.
* Press Enter once (this jumps to a new, empty line).
* Press Ctrl + Z on your keyboard.
* Press Enter one last time.

A `browser.json` file will be generated in your folder. Never share this file or upload it to GitHub!

## Usage

### Synchronize Playlists
Run the main sync tool:
```bash
python sync_tool.py
```
* Use the Spacebar to select the playlists you want to sync, and press Enter to confirm.
* Tracks that cannot be found on YouTube Music will be listed in `missing_tracks.txt`.

### Clean Up Duplicates
Run the cleanup tool:
```bash
python cleanup_duplicates.py
```
* Select the playlist you want to analyze.
* The script will list all detected duplicates and ask for your explicit confirmation before permanently deleting them.