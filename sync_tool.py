import os
import json
import questionary
import ytmusicapi.auth.auth_parse
from ytmusicapi.auth.types import AuthType
from ytmusicapi import YTMusic
from dotenv import load_dotenv
from plexapi.server import PlexServer
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize Colorama for terminal colors
init()

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')

CACHE_FILE = 'match_cache.json'
MISSING_FILE = 'missing_tracks.txt'
BATCH_SIZE = 50

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

def save_missing_tracks(missing_list):
    if not missing_list:
        return
    with open(MISSING_FILE, 'w', encoding='utf-8') as f:
        for track in missing_list:
            f.write(f"{track}\n")

def setup_ytmusic():
    with open("browser.json", "r", encoding="utf-8") as f:
        auth_dict = json.load(f)
    return YTMusic(auth=auth_dict)

def get_yt_rating(plex_rating):
    if plex_rating is None:
        return 'INDIFFERENT'
    if plex_rating >= 8.0:
        return 'LIKE'
    if plex_rating <= 2.0:
        return 'DISLIKE'
    return 'INDIFFERENT'

def match_song(yt, artist, title, duration_ms, cache):
    cache_key = f"{artist} - {title}"
    
    if cache_key in cache:
        video_id = cache[cache_key]
        if video_id:
            tqdm.write(f"Loaded from cache: {artist} - {title}")
            return video_id
        else:
            tqdm.write(f"{Fore.RED}Cache (Not found on YT): {artist} - {title}{Style.RESET_ALL}")
            return None
    
    results = yt.search(f"{artist} {title}", filter="songs", limit=5)
    target_duration = duration_ms / 1000
    
    for result in results:
        yt_duration = result.get('duration_seconds')
        if yt_duration and abs(target_duration - yt_duration) <= 5:
            tqdm.write(f"{Fore.GREEN}Match found! ({result['title']}){Style.RESET_ALL}")
            cache[cache_key] = result['videoId']
            return result['videoId']
            
    tqdm.write(f"{Fore.RED}No suitable match found: {artist} - {title}{Style.RESET_ALL}")
    cache[cache_key] = None
    return None

def sync_playlists():
    if not PLEX_URL or not PLEX_TOKEN:
        print("Error: Plex variables missing in .env file.")
        return

    print("Connecting to Plex and YouTube Music...")
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    yt = setup_ytmusic()
    cache = load_cache()
    
    all_playlists = [pl for pl in plex.playlists() if pl.playlistType == 'audio']
    choices = [pl.title for pl in all_playlists]
    
    selected_titles = questionary.checkbox(
        "Select playlists to sync (Space to select, Enter to confirm):",
        choices=choices
    ).ask()
    
    if not selected_titles:
        print("No playlist selected. Aborting.")
        return

    print("\nLoading existing YouTube Music playlists (for comparison)...")
    yt_playlists = yt.get_library_playlists(limit=1000)
    yt_playlist_dict = {p['title']: p['playlistId'] for p in yt_playlists}

    missing_tracks = []

    for title in selected_titles:
        pl = next((p for p in all_playlists if p.title == title), None)
        if pl:
            print(f"\n*** Processing playlist: {pl.title} ***")
            
            yt_playlist_id = yt_playlist_dict.get(pl.title)
            if yt_playlist_id:
                print(f"Playlist '{pl.title}' exists. Loading existing tracks...")
                existing_pl = yt.get_playlist(yt_playlist_id, limit=None)
                existing_video_ids = set([track['videoId'] for track in existing_pl.get('tracks', []) if track.get('videoId')])
            else:
                print(f"Creating new playlist '{pl.title}'...")
                yt_playlist_id = yt.create_playlist(title=pl.title, description="Synced from Plex", privacy_status="PRIVATE")
                yt_playlist_dict[pl.title] = yt_playlist_id
                existing_video_ids = set()

            batch = []
            total_synced = 0
            tracks = pl.items()
            
            pbar = tqdm(total=len(tracks), desc="Progress", unit="Song", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")
            
            for track in tracks:
                artist = track.originalTitle if track.originalTitle else track.grandparentTitle
                song_title = track.title
                duration_ms = track.duration
                
                # Format duration for the missing tracks file
                duration_str = "Unknown"
                if duration_ms:
                    mins = duration_ms // 60000
                    secs = (duration_ms % 60000) // 1000
                    duration_str = f"{mins}:{secs:02d}"
                
                video_id = match_song(yt, artist, song_title, duration_ms, cache)
                
                if video_id:
                    yt_rating = get_yt_rating(track.userRating)
                    if yt_rating != 'INDIFFERENT' or track.userRating is not None:
                        yt.rate_song(video_id, yt_rating)

                    if video_id not in existing_video_ids:
                        batch.append(video_id)
                        existing_video_ids.add(video_id)
                else:
                    missing_tracks.append(f"{artist} - {song_title} | {duration_str} (Playlist: {pl.title})")
                    # Immediate save when a track is missing
                    save_missing_tracks(missing_tracks)
                
                if len(batch) >= BATCH_SIZE:
                    yt.add_playlist_items(yt_playlist_id, batch)
                    total_synced += len(batch)
                    tqdm.write(f"-> Intermediate save: {total_synced} new tracks added to playlist.")
                    batch = []
                    save_cache(cache)
                
                pbar.update(1)

            pbar.close()

            if batch:
                yt.add_playlist_items(yt_playlist_id, batch)
                total_synced += len(batch)
                print(f"-> Final batch: {total_synced} tracks added in total.")
                save_cache(cache)
                save_missing_tracks(missing_tracks)
            elif total_synced == 0:
                print("-> Playlist is already up to date. No new tracks added.")

            save_cache(cache)
            save_missing_tracks(missing_tracks)
            print(f"Finished processing playlist '{pl.title}'.")

    if missing_tracks:
        print(f"\n{Fore.RED}*** Sync complete. {len(missing_tracks)} tracks were not found ***{Style.RESET_ALL}")
        print(f"Details have been continuously saved to '{MISSING_FILE}'.")
    else:
        print(f"\n{Fore.GREEN}*** Sync complete. All tracks matched successfully! ***{Style.RESET_ALL}")
        if os.path.exists(MISSING_FILE):
            os.remove(MISSING_FILE)

if __name__ == "__main__":
    sync_playlists()