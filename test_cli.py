from ytmusicapi import YTMusic

try:
    # Lade die vom CLI generierte Datei
    yt = YTMusic("browser.json")
    
    playlists = yt.get_library_playlists(limit=2)
    print("Erfolg! Verbindung steht.")
    print(f"Gefundene Playlists: {len(playlists)}")
except Exception as e:
    print(f"Fehler: {e}")