import json
import ytmusicapi.auth.auth_parse
from ytmusicapi.auth.types import AuthType
from ytmusicapi import YTMusic

# BUGFIX: Jetzt mit dem exakt richtigen Funktionsnamen der Library.
# Das zwingt die Library unwiderruflich in den Browser-Authentifizierungs-Modus.
ytmusicapi.auth.auth_parse.determine_auth_type = lambda *args, **kwargs: AuthType.BROWSER

def test_connection():
    try:
        # Wir laden die Daten manuell, um Fehler beim File-Parsing der Library auszuschliessen
        with open("browser.json", "r", encoding="utf-8") as f:
            auth_dict = json.load(f)
            
        # Initialisierung direkt mit dem Dictionary anstatt dem Dateipfad
        yt = YTMusic(auth=auth_dict)
        
        playlists = yt.get_library_playlists(limit=2)
        
        print("Erfolg! Verbindung zu YouTube Music steht.")
        print(f"Gefundene Playlists: {len(playlists)}")
        for pl in playlists:
            print(f"- {pl['title']}")
            
    except Exception as e:
        print(f"Fehler beim Verbinden: {e}")

if __name__ == "__main__":
    test_connection()