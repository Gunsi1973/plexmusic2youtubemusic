import os
from dotenv import load_dotenv
from plexapi.server import PlexServer

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

def analyze_playlists():
    if not PLEX_URL or not PLEX_TOKEN:
        print("Fehler: Umgebungsvariablen fehlen.")
        return

    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        playlists = [pl for pl in plex.playlists() if pl.playlistType == 'audio']
        
        print("Gefundene Playlists im Detail:")
        for index, pl in enumerate(playlists):
            typ = "Smart" if pl.smart else "Statisch"
            print(f"{index}: {pl.title} ({pl.leafCount} Tracks) [{typ}]")
            
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    analyze_playlists()