import json
import questionary
from ytmusicapi import YTMusic

def setup_ytmusic():
    with open("browser.json", "r", encoding="utf-8") as f:
        auth_dict = json.load(f)
    return YTMusic(auth=auth_dict)

def cleanup_playlists():
    print("Connecting to YouTube Music...")
    yt = setup_ytmusic()

    print("Loading your playlists...")
    playlists = yt.get_library_playlists(limit=100)
    choices = [pl['title'] for pl in playlists]

    selected_titles = questionary.checkbox(
        "Select playlists to clean up (Space to select, Enter to confirm):",
        choices=choices
    ).ask()

    if not selected_titles:
        print("No playlist selected. Aborting.")
        return

    for title in selected_titles:
        print(f"\n{'-'*40}")
        print(f"*** Analyzing playlist: {title} ***")
        pl_info = next((p for p in playlists if p['title'] == title), None)

        if not pl_info:
            continue

        playlist_id = pl_info['playlistId']
        # limit=None forces loading of all tracks in the playlist
        full_playlist = yt.get_playlist(playlist_id, limit=None)
        tracks = full_playlist.get('tracks', [])

        seen_video_ids = set()
        duplicates_to_remove = []

        for track in tracks:
            vid = track.get('videoId')
            svid = track.get('setVideoId')
            
            # Extract title and artist for display
            song_title = track.get('title', 'Unknown Title')
            artists = track.get('artists', [{'name': 'Unknown Artist'}])
            artist_name = artists[0]['name'] if artists else 'Unknown Artist'

            if not vid or not svid:
                continue

            if vid in seen_video_ids:
                # Mark duplicate for display and removal
                duplicates_to_remove.append({
                    'videoId': vid, 
                    'setVideoId': svid,
                    'display_name': f"{artist_name} - {song_title}"
                })
            else:
                # Remember unique song
                seen_video_ids.add(vid)

        if duplicates_to_remove:
            print(f"\nFound {len(duplicates_to_remove)} duplicates:")
            for index, dup in enumerate(duplicates_to_remove, 1):
                print(f"  {index}. {dup['display_name']}")
            
            print() # Blank line for readability
            
            # Safety confirmation before deletion
            confirm = questionary.confirm(
                "Do you want to permanently delete these duplicates from the playlist?"
            ).ask()

            if confirm:
                # API expects only videoId and setVideoId
                api_payload = [{'videoId': d['videoId'], 'setVideoId': d['setVideoId']} for d in duplicates_to_remove]
                yt.remove_playlist_items(playlist_id, api_payload)
                print("-> Duplicates successfully removed.")
            else:
                print("-> Cleanup canceled. No changes were made to the playlist.")
        else:
            print("-> No duplicates found in this playlist.")

if __name__ == "__main__":
    cleanup_playlists()