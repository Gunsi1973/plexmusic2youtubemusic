from ytmusicapi import YTMusic
try:
    # Passe den Dateinamen an, falls er anders generiert wurde
    yt = YTMusic("oauth.json") 
    print("YT Music Login: OK")
except Exception as e:
    print(f"Fehler: {e}")