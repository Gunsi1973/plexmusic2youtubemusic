import json
import questionary
from ytmusicapi import YTMusic
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize Colorama
init()

def setup_ytmusic():
    with open("browser.json", "r", encoding="utf-8") as f:
        auth_dict = json.load(f)
    return YTMusic(auth=auth_dict)

def rate_playlists():
    print("Connecting to YouTube Music...")
    try:
        yt = setup_ytmusic()
    except Exception as e:
        print(f"{Fore.RED}Error loading authentication: {e}{Style.RESET_ALL}")
        return

    print("Loading your playlists...")
    playlists = yt.get_library_playlists(limit=1000)
    choices = [pl['title'] for pl in playlists]

    selected_titles = questionary.checkbox(
        "Select playlists (Space to select, Enter to confirm):",
        choices=choices
    ).ask()

    if not selected_titles:
        print("No playlist selected. Aborting.")
        return

    for title in selected_titles:
        print(f"\n*** Analyzing playlist: {title} ***")
        pl_info = next((p for p in playlists if p['title'] == title), None)

        if not pl_info:
            continue

        playlist_id = pl_info['playlistId']
        
        # Force loading all tracks in the playlist
        full_playlist = yt.get_playlist(playlist_id, limit=None)
        tracks = full_playlist.get('tracks', [])
        
        if not tracks:
            print("Playlist is empty or could not be loaded.")
            continue

        updated_count = 0
        
        # Initialize progress bar
        pbar = tqdm(total=len(tracks), desc="Progress", unit="Song", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")

        for track in tracks:
            vid = track.get('videoId')
            like_status = track.get('likeStatus')
            
            # Check if video ID exists and thumbs up is not already given
            if vid and like_status != 'LIKE':
                yt.rate_song(vid, 'LIKE')
                updated_count += 1
            
            pbar.update(1)

        pbar.close()
        
        if updated_count > 0:
            print(f"{Fore.GREEN}Finished with '{title}'. Applied {updated_count} new thumbs up.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Finished with '{title}'. All tracks already had a thumbs up.{Style.RESET_ALL}")

if __name__ == "__main__":
    rate_playlists()